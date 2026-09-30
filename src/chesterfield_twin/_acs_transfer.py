"""Isolated, single-request transport. IPC contains secrets; stdout never does."""
import json
import ssl
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

LIMIT = 20_000_000
FIELDS = ['NAME'] + [p + s for p in ('S1901_C01_012', 'S1901_C01_001', 'S1701_C03_001')
                     for s in ('E', 'M', 'EA', 'MA')]
BASE = 'https://api.census.gov/data/2023/acs/acs5/subject'


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def sanitize(url):
    parts = urllib.parse.urlsplit(url)
    # Preserve actual encoded public selectors, removing only the key component.
    query = '&'.join(x for x in parts.query.split('&')
                     if urllib.parse.unquote_plus(x.split('=', 1)[0]) != 'key')
    return urllib.parse.urlunsplit(parts._replace(query=query))


def echoed(raw, key):
    forms = {key, urllib.parse.quote(key, safe=''), urllib.parse.quote_plus(key, safe='')}
    text = raw.decode('utf-8', errors='replace')
    if any(form in text for form in forms):
        return True
    if key in urllib.parse.unquote(text):
        return True
    try:
        value = json.loads(raw)
    except (ValueError, UnicodeError, RecursionError):
        return False
    def walk(item):
        if isinstance(item, str):
            return key in item or key in urllib.parse.unquote(item)
        if isinstance(item, list):
            return any(walk(x) for x in item)
        if isinstance(item, dict):
            return any(walk(k) or walk(v) for k, v in item.items())
        return False
    return walk(value)


def transfer(key):
    started = time.monotonic()
    url = BASE + '?' + urllib.parse.urlencode([
        ('get', ','.join(FIELDS)), ('for', 'tract:*'), ('in', 'state:51 county:041'), ('key', key)])
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect(),
        urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    request = urllib.request.Request(url, headers={'Accept': 'application/json',
                                                  'Accept-Encoding': 'identity'})
    with opener.open(request, timeout=60) as response:
        final = response.geturl()
        if response.status != 200 or final != url:
            raise ValueError()
        media = response.headers.get('Content-Type', '')
        if media.split(';', 1)[0].strip().lower() != 'application/json':
            raise ValueError()
        if response.headers.get('Content-Encoding', 'identity').strip().lower() != 'identity':
            raise ValueError()
        lengths = response.headers.get_all('Content-Length', [])
        if len(lengths) > 1 or (lengths and response.headers.get('Transfer-Encoding')):
            raise ValueError()
        length = response.headers.get('Content-Length')
        if length is not None and (not length.isdecimal() or int(length) > LIMIT):
            raise ValueError()
        chunks, size = [], 0
        while True:
            chunk = response.read(min(65536, LIMIT + 1 - size))
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
            if size > LIMIT or time.monotonic() - started >= 60:
                raise ValueError()
        raw = b''.join(chunks)
        if not raw or (length is not None and len(raw) != int(length)):
            raise ValueError()
        metadata = dict(request_url=sanitize(request.full_url), final_url=sanitize(final),
            retrieved_at=datetime.now(timezone.utc).isoformat(), status_code=200,
            media_type=media, elapsed_seconds=time.monotonic() - started)
        if echoed(raw, key) or echoed(json.dumps(metadata).encode(), key):
            raise ValueError()
        return metadata, raw


def main():
    try:
        key = sys.stdin.buffer.read(257).decode('ascii')
        if not 1 <= len(key) <= 256 or any(not 33 <= ord(c) <= 126 for c in key):
            raise ValueError()
        metadata, raw = transfer(key)
        header = json.dumps(metadata, allow_nan=False).encode()
        if len(header) > 8192:
            raise ValueError()
        sys.stdout.buffer.write(header + b'\n' + raw)
        sys.stdout.buffer.flush()
    except BaseException:
        # Never forward response bodies, Location, exception text, or traceback.
        sys.exit(1)


if __name__ == '__main__':
    main()
