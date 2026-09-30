"""Mock HTTP and real isolated child cancellation, entirely offline."""
import io
import json
import subprocess
import sys
import time
import urllib.error
from email.message import Message
from urllib.parse import parse_qs, urlsplit

import pytest

from chesterfield_twin import _acs_transfer as t
from chesterfield_twin import acquisition as a

KEY = 'synthetic-secret-XYZ'


class Response:
    def __init__(self, raw=b'[["safe"]]', *, status=200, media='application/json',
                 encoding='identity', length=None, final=None):
        self.body = io.BytesIO(raw)
        self.status = status
        self.headers = Message()
        self.headers['Content-Type'] = media
        self.headers['Content-Encoding'] = encoding
        if length is not None:
            self.headers['Content-Length'] = length
        self.final = final
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    def geturl(self):
        return self.final or self.request.full_url
    def read(self, amount):
        return self.body.read(amount)


def install(monkeypatch, response):
    requests, handlers = [], []
    class Opener:
        def open(self, request, timeout):
            requests.append(request)
            assert timeout == 60
            if isinstance(response, Exception):
                raise response
            response.request = request
            return response
    def build(*items):
        handlers.extend(items)
        return Opener()
    monkeypatch.setattr(t.urllib.request, 'build_opener', build)
    return requests, handlers


def test_exact_single_request_proxy_disabled_validated_tls(monkeypatch):
    requests, handlers = install(monkeypatch, Response())
    metadata, raw = t.transfer(KEY)
    assert raw == b'[["safe"]]' and len(requests) == 1
    query = parse_qs(urlsplit(requests[0].full_url).query)
    assert query == {'get': [','.join(t.FIELDS)], 'for': ['tract:*'],
                     'in': ['state:51 county:041'], 'key': [KEY]}
    assert requests[0].get_header('Accept-encoding') == 'identity'
    assert isinstance(handlers[0], t.urllib.request.ProxyHandler) and handlers[0].proxies == {}
    context = handlers[2]._context
    assert context.check_hostname and context.verify_mode == t.ssl.CERT_REQUIRED
    assert KEY not in json.dumps(metadata)
    assert metadata['request_url'] == t.sanitize(requests[0].full_url)
    assert t.NoRedirect().redirect_request(None, None, 302, None, None, 'https://evil') is None


@pytest.mark.parametrize('response', [Response(status=302), Response(status=500),
    Response(media='text/html'), Response(encoding='gzip'), Response(length='1x'),
    Response(length=str(t.LIMIT + 1)), Response(length='100'),
    Response(final='https://evil.invalid/'), urllib.error.URLError('synthetic TLS failure'),
    urllib.error.HTTPError(t.BASE, 302, 'redirect', {'Location': 'https://evil'}, None)])
def test_error_transport_no_success(monkeypatch, response):
    requests, _ = install(monkeypatch, response)
    with pytest.raises(Exception):
        t.transfer(KEY)
    assert len(requests) == 1


@pytest.mark.parametrize('mode', ['duplicate_length', 'length_and_encoding', 'cap', 'slow_drip'])
def test_transfer_bounds(monkeypatch, mode):
    response = Response(length='10')
    if mode == 'duplicate_length':
        response.headers['Content-Length'] = '10'
    elif mode == 'length_and_encoding':
        response.headers['Transfer-Encoding'] = 'chunked'
    elif mode == 'cap':
        monkeypatch.setattr(t, 'LIMIT', 3)
        del response.headers['Content-Length']
    else:
        clock = iter([0, 61])
        monkeypatch.setattr(t.time, 'monotonic', lambda: next(clock))
    install(monkeypatch, response)
    with pytest.raises(ValueError):
        t.transfer(KEY)


@pytest.mark.parametrize('body', [KEY.encode(), KEY.replace('-', '%2d').encode(),
    json.dumps({'field': KEY}).encode(),
    ('["' + ''.join('\\u%04x' % ord(c) for c in KEY) + '"]').encode()])
def test_child_rejects_credential_echo(monkeypatch, body):
    install(monkeypatch, Response(body))
    with pytest.raises(ValueError):
        t.transfer(KEY)


@pytest.mark.parametrize('phase', ['dns', 'headers', 'drip'])
def test_actual_helper_process_timeout_kill_reap(monkeypatch, phase):
    original = subprocess.Popen
    processes = []
    def launch(argv, **kwargs):
        assert argv[1] == '-I' and argv[-1].endswith('_acs_transfer.py')
        assert KEY not in repr(argv) + repr(kwargs['env'])
        assert kwargs['stderr'] == subprocess.DEVNULL
        assert not any('proxy' in k.lower() or 'key' in k.lower() for k in kwargs['env'])
        # The substitute is an actual isolated child but never opens a socket.
        # Execute the actual helper entry point with only its network function replaced.
        body = 'time.sleep(30)'
        if phase == 'drip':
            body = 'sys.stdout.buffer.write(b"x");sys.stdout.buffer.flush();time.sleep(30)'
        definition = 'def offline(key):\n    ' + body
        code = (f'import runpy,sys,time;scope=runpy.run_path({argv[-1]!r});'
                f'exec({definition!r},globals());'
                'scope["main"].__globals__["transfer"]=offline;scope["main"]()')
        process = original([sys.executable, '-I', '-c', code], **kwargs)
        processes.append(process)
        return process
    monkeypatch.setattr(a.subprocess, 'Popen', launch)
    monkeypatch.setattr(a, 'DEADLINE', 0.15)
    monkeypatch.setenv('SSLKEYLOGFILE', '/should/not/exist')
    monkeypatch.setenv('HTTPS_PROXY', 'http://evil.invalid')
    monkeypatch.setenv('CDT_CENSUS_API_KEY', KEY)
    started = time.monotonic()
    with pytest.raises(a.AcquisitionError, match='timeout') as error:
        a._transport(KEY)
    assert time.monotonic() - started < 3
    assert processes[0].poll() is not None
    assert processes[0].stdin.closed and processes[0].stdout.closed
    assert KEY not in str(error.value)


def test_parent_protocol_echo_rejected_and_child_environment(monkeypatch):
    original = subprocess.Popen
    def launch(argv, **kwargs):
        code = 'import sys;value=sys.stdin.buffer.read();sys.stdout.buffer.write(value)'
        return original([sys.executable, '-I', '-c', code], **kwargs)
    monkeypatch.setattr(a.subprocess, 'Popen', launch)
    with pytest.raises(a.AcquisitionError, match='credential_echo'):
        a._transport(KEY)


def test_parent_total_elapsed_includes_launch(monkeypatch):
    original = subprocess.Popen
    def launch(argv, **kwargs):
        metadata = {'elapsed_seconds': 0.001}
        payload = json.dumps(metadata).encode() + b'\n[]'
        code = ('import sys,time;sys.stdin.buffer.read();time.sleep(.05);'
                f'sys.stdout.buffer.write({payload!r})')
        return original([sys.executable, '-I', '-c', code], **kwargs)
    monkeypatch.setattr(a.subprocess, 'Popen', launch)
    metadata, raw = a._transport(KEY)
    assert metadata['elapsed_seconds'] >= 0.05 and raw == b'[]'


def test_interrupt_kills_reaps(monkeypatch):
    original = subprocess.Popen
    processes = []
    def launch(argv, **kwargs):
        process = original([sys.executable, '-I', '-c', 'import time;time.sleep(30)'], **kwargs)
        processes.append(process)
        return process
    monkeypatch.setattr(a.subprocess, 'Popen', launch)
    monkeypatch.setattr(a.selectors.DefaultSelector, 'select',
                        lambda *args: (_ for _ in ()).throw(KeyboardInterrupt()))
    with pytest.raises(KeyboardInterrupt):
        a._transport(KEY)
    assert processes[0].poll() is not None


def test_actual_helper_suppresses_secret_exception_stdout_stderr():
    helper = str(a.Path(t.__file__).resolve())
    code = (f'import runpy;scope=runpy.run_path({helper!r});'
            'exec("def fail(key):\\n    raise RuntimeError(key)",globals());'
            'scope["main"].__globals__["transfer"]=fail;scope["main"]()')
    result = subprocess.run([sys.executable, '-I', '-c', code], input=KEY.encode(),
                            capture_output=True, env={}, timeout=3, check=False)
    assert result.returncode == 1
    assert result.stdout == b'' and result.stderr == b''


def test_parent_stdout_protocol_is_bounded(monkeypatch):
    original = subprocess.Popen
    processes = []
    def launch(argv, **kwargs):
        code = 'import sys,time;sys.stdin.buffer.read();sys.stdout.buffer.write(b"x"*9000);sys.stdout.buffer.flush();time.sleep(30)'
        process = original([sys.executable, '-I', '-c', code], **kwargs)
        processes.append(process)
        return process
    monkeypatch.setattr(a.subprocess, 'Popen', launch)
    monkeypatch.setattr(a, 'LIMIT', 1)
    with pytest.raises(a.AcquisitionError, match='transfer'):
        a._transport(KEY)
    assert processes[0].poll() is not None
