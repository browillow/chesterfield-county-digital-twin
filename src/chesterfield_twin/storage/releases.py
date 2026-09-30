"""Verified, reproducible first-slice sealing. Never changes the active pointer."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import re
import sqlite3
import subprocess
import tomllib
from pathlib import Path

from pydantic import ValidationError

from chesterfield_twin.domain.candidates import digest
from chesterfield_twin.domain.releases import (
    ReleaseBuildReport,
    ReleaseBuildResult,
    ReleaseContent,
    ReleaseEdge,
    ReleaseManifest,
    ReleaseNode,
    ReleaseReportContent,
    ReleaseSelection,
)
from chesterfield_twin.domain.validation_reports import ReportIssue
from chesterfield_twin.sources.validation import validate_slice
from chesterfield_twin.storage import StorageError
from chesterfield_twin.storage.staging import _ADAPTERS, CandidateStaging, _json
from chesterfield_twin.storage.validation import _SOURCES, CandidateValidation

_PREFIXES = ('src/', 'scripts/', 'source_specs/', 'frontend/src/', 'frontend/public/')
_FILES = {'pyproject.toml', 'uv.lock', '.python-version', 'openapi.json',
          '.node-version', 'frontend/package.json', 'frontend/package-lock.json', 'frontend/index.html'}
_CONFIG = re.compile(r'^(?:frontend/)?(?:vite|vitest|tsconfig|eslint|postcss|tailwind|webpack|rollup|babel)[^/]*$')
_MODULES = ('sources/acs.py', 'sources/boundaries.py', 'sources/documents.py',
            'sources/common.py', 'sources/validation.py', 'domain/candidates.py',
            'domain/contracts.py', 'domain/releases.py', 'domain/validation_reports.py',
            'storage/staging.py', 'storage/validation.py', 'storage/releases.py',
            'storage/__init__.py', 'config.py')

_EXECUTING = {m: hashlib.sha256((Path(__file__).parents[1] / m).read_bytes()).hexdigest()
              for m in _MODULES}


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _allowed(path):
    return path.startswith(_PREFIXES) or path in _FILES or bool(_CONFIG.fullmatch(path))


class ReleaseBuilder:
    def __init__(self, root: Path, repository_root: Path):
        self.staging = CandidateStaging(root)
        self.repository_root = Path(repository_root)

    def _git(self, *args):
        try:
            return subprocess.check_output(('git', '-C', str(self.repository_root), *args),
                                           stderr=subprocess.DEVNULL)
        except (OSError, subprocess.CalledProcessError) as exc:
            raise StorageError('build repository is unavailable') from exc

    def _snapshot(self, *, retain=True):
        names = sorted(set(self._git('ls-files', '--cached', '--others',
                                     '--exclude-standard', '-z').decode().split('\0')) - {''})
        files = []
        for name in names:
            if not _allowed(name):
                continue
            path = Path(name)
            if path.is_absolute() or '..' in path.parts:
                raise StorageError('unsafe build input path')
            target = self.repository_root / path
            if any(p.is_symlink() for p in (target, *target.parents)):
                raise StorageError('symlink build input is forbidden')
            if not target.exists():
                files.append({'path': name, 'deleted': True})
                continue
            data = target.read_bytes()
            sha = self.staging.objects.put(data) if retain else _sha(data)
            files.append({'path': name, 'deleted': False, 'sha256': sha, 'byte_length': len(data)})
        for entry in files:
            module = entry['path'].removeprefix('src/chesterfield_twin/')
            if module in _EXECUTING and entry.get('sha256') != _EXECUTING[module]:
                raise StorageError('snapshot differs from executing implementation')
        present = {f['path'] for f in files if not f['deleted']}
        required = _FILES | {'src/chesterfield_twin/' + m for m in _MODULES}
        required |= {'src/chesterfield_twin/storage/migrations/baseline/' + n for n in
                     ('001_initial.sql', '002_candidate_staging.sql', '003_candidate_validation.sql',
                      '004_release_closure.sql')}
        if not required <= present:
            raise StorageError('required code or dependency input is missing: ' +
                               ', '.join(sorted(required - present)))
        return {'head': self._git('rev-parse', 'HEAD').decode().strip(),
                'dirty': bool(self._git('status', '--porcelain', '--untracked-files=all')),
                'allowlist': {'prefixes': list(_PREFIXES), 'files': sorted(_FILES),
                              'configuration_pattern': _CONFIG.pattern},
                'files': files, 'manifest_sha256': digest(files)}

    def _verify_snapshot(self, snapshot):
        files = snapshot['files']
        if files != sorted(files, key=lambda f: f['path']) or digest(files) != snapshot['manifest_sha256']:
            raise StorageError('code file manifest is invalid')
        for entry in files:
            if not _allowed(entry['path']) or '..' in Path(entry['path']).parts:
                raise StorageError('unsafe retained build input')
            if not entry['deleted']:
                if len(self.staging.objects.read(entry['sha256'])) != entry['byte_length']:
                    raise StorageError('retained build input length mismatch')

    def _runtime(self):
        packages = sorted({(d.metadata['Name'], d.version) for d in importlib.metadata.distributions()})
        return {'python': platform.python_version(), 'sqlite': sqlite3.sqlite_version,
                'packages': [{'name': n, 'version': v} for n, v in packages],
                'lock_sync_verified': False}

    def _closure(self, db, report, snapshot, runtime):
        self._verify_snapshot(snapshot)
        files = {f['path']: f for f in snapshot['files'] if not f['deleted']}
        uv = tomllib.loads(self.staging.objects.read(files['uv.lock']['sha256']).decode())
        npm = json.loads(self.staging.objects.read(files['frontend/package-lock.json']['sha256']))
        project = tomllib.loads(self.staging.objects.read(files['pyproject.toml']['sha256']).decode())
        package = json.loads(self.staging.objects.read(files['frontend/package.json']['sha256']))
        if (not isinstance(npm, dict) or not isinstance(package, dict) or
                uv.get('version') != 1 or not uv.get('requires-python') or
                not isinstance(uv.get('package'), list) or not uv['package'] or
                any(not isinstance(p, dict) or not p.get('name') or not p.get('version')
                    for p in uv['package']) or
                npm.get('lockfileVersion') != 3 or not isinstance(npm.get('packages'), dict) or
                npm.get('name') != package.get('name') or
                not isinstance(npm['packages'].get(''), dict) or
                npm['packages'][''].get('dependencies') != package.get('dependencies') or
                not isinstance(project.get('project'), dict) or
                not project['project'].get('dependencies')):
            raise StorageError('retained dependency manifests or locks are invalid')
        nodes, edges = {}, set()

        def node(kind, key, payload):
            item = ReleaseNode(kind=kind, key=key, payload=payload)
            old = nodes.get((kind, key))
            if old is not None and old != item:
                raise StorageError('conflicting closure identity')
            nodes[kind, key] = item
            return item

        def edge(a, role, b):
            edges.add((a.node_id, role, b.node_id))

        batches, imports, candidates = {}, [], []
        for pin in report.content.inputs:
            batch = self.staging._read_import(db, report.content.run_id, pin.import_id)
            batches[_SOURCES[pin.source_id]] = batch
            candidates.extend(batch.candidates)
            row = dict(db.execute('SELECT * FROM staging_import WHERE import_id=?',
                                  (pin.import_id,)).fetchone())
            row['version_ids'] = [c.fingerprint for c in batch.candidates]
            if (tuple(row['version_ids']) != pin.version_ids or
                    row['membership_sha256'] != pin.membership_sha256):
                raise StorageError('candidate report membership changed')
            p = batch.candidates[0].provenance
            if (pin.run_id != row['run_id'] or pin.synthetic != report.content.synthetic or
                    pin.retrieval_id != row['retrieval_id'] or pin.source_id != row['source_id'] or
                    pin.raw_sha256 != p.artifact_sha256 or pin.spec_sha256 != row['spec_sha256'] or
                    pin.transform_id != row['transform_id'] or not pin.verified or
                    p.synthetic != report.content.synthetic):
                raise StorageError('candidate report input pins differ')
            imports.append(row)
        validated = validate_slice(*(batches[s] for s in ('acs', 'boundary', 'document')),
                                   allow_synthetic=report.content.synthetic)
        issues = tuple(ReportIssue(code=i.code, message=i.message, severity=i.severity,
                                   locator=i.locator) for i in validated.issues)
        if not validated.valid or issues != report.content.issues:
            raise StorageError('current slice validation differs from candidate report')
        if {c.fingerprint for c in validated.candidates} != {c.fingerprint for c in candidates}:
            raise StorageError('validated candidate set differs')
        sources, specs, raws, events, transforms = {}, {}, {}, {}, {}
        for label, batch in batches.items():
            p = batch.candidates[0].provenance
            spec_row = dict(db.execute('SELECT * FROM artifact WHERE sha256=?',
                                       (p.spec_sha256,)).fetchone())
            raw_row = dict(db.execute('SELECT * FROM artifact WHERE sha256=?',
                                      (p.artifact_sha256,)).fetchone())
            spec_row.pop('created_at', None)
            raw_row.pop('created_at', None)
            spec_bytes = self.staging.objects.read(p.spec_sha256)
            spec = tomllib.loads(spec_bytes.decode())
            replay = _ADAPTERS[label](self.staging.objects.read(p.artifact_sha256),
                p.retrieval, spec_bytes, synthetic=report.content.synthetic)
            if replay != batch:
                raise StorageError('retained raw bytes do not reproduce selected candidates')
            specs[label] = spec
            if spec['source_id'] != p.source_id:
                raise StorageError('retained source spec identity mismatch')
            sn = node('spec', p.spec_sha256, {'registration': spec_row,
                      'toml': spec_bytes.decode(), 'retention': p.retention,
                      'redistribution': p.redistribution})
            rn = node('raw', p.artifact_sha256, {'registration': raw_row,
                      'retention': p.retention, 'redistribution': p.redistribution})
            source = node('source', p.source_id, {'specification': spec,
                          'spec_sha256': p.spec_sha256, 'retention': p.retention,
                          'redistribution': p.redistribution})
            edge(source, 'spec', sn)
            imported = next(i for i in imports if i['source_id'] == p.source_id)
            event = dict(db.execute('SELECT * FROM retrieval WHERE retrieval_id=?',
                                    (imported['retrieval_id'],)).fetchone())
            event['metadata'] = json.loads(event.pop('metadata_json'))
            en = node('retrieval', event['retrieval_id'], event)
            edge(en, 'raw', rn)
            adapter = {'acs': 'acs.py', 'boundary': 'boundaries.py', 'document': 'documents.py'}[label]
            paths = ['sources/' + adapter, 'sources/common.py', 'sources/validation.py',
                     'domain/candidates.py', 'domain/contracts.py']
            implementation = {m: files['src/chesterfield_twin/' + m]['sha256'] for m in paths}
            # IDs are fixed adapter constants, not caller declarations.
            expected = {'acs': 'acs-subject/1', 'boundary': 'boundaries/1',
                        'document': 'county-budget-pypdf-6.1.1/1'}[label]
            if p.transform_id != expected:
                raise StorageError('unsupported transform identity')
            tn = node('transform', p.transform_id, {'implementation': implementation})
            sources[label], raws[label], events[label], transforms[label] = source, rn, en, tn
        metric_nodes = {}
        for definition in specs['acs']['metrics']:
            payload = dict(definition, reference_period=specs['acs']['reference_period'],
                           publication_vintage=specs['acs']['publication_vintage'],
                           source_id=sources['acs'].key, spec_sha256=batches['acs'].candidates[0].provenance.spec_sha256)
            mn = node('metric', definition['code'], payload)
            metric_nodes[definition['code']] = mn
            edge(mn, 'source', sources['acs'])
            edge(mn, 'spec', nodes['spec', payload['spec_sha256']])
        ds = specs['document']
        document = node('document', sources['document'].key, {
            'title': ds['title'], 'fiscal_period': ds['fiscal_year'],
            'geographic_scope': ['51041', '51570'], 'scope_caveat': ds['scope_caveat'],
            'raw_sha256': raws['document'].key,
            'spec_sha256': batches['document'].candidates[0].provenance.spec_sha256,
            'redistribution': ds['redistribution'], 'locators': ds['locators']})
        for role, target in (('raw', raws['document']), ('source', sources['document']),
                             ('spec', nodes['spec', document.payload['spec_sha256']])):
            edge(document, role, target)
        boundary_nodes = {}
        for c in candidates:
            stored = dict(db.execute('SELECT version_id,kind,synthetic,payload_json FROM version '
                                     'WHERE version_id=?', (c.fingerprint,)).fetchone())
            stored['payload'] = json.loads(stored.pop('payload_json'))
            cn = node('candidate', c.fingerprint, stored)
            label = _SOURCES[c.provenance.source_id]
            for role, target in (('source', sources[label]), ('raw', raws[label]),
                                 ('spec', nodes['spec', c.provenance.spec_sha256]),
                                 ('retrieval', events[label]), ('transform', transforms[label])):
                edge(cn, role, target)
            if c.kind == 'boundary':
                boundary_nodes[c.geography_id] = cn
            elif c.kind == 'document_excerpt':
                locator = next((loc for loc in ds['locators'] if loc['pdf_page'] == c.locator.pdf_page), None)
                if (c.title != ds['title'] or c.reference_period != ds['fiscal_year'] or
                        c.scope_caveat != ds['scope_caveat'] or locator is None or
                        str(locator['printed_page']) != c.locator.printed_page or
                        locator['heading'] != c.locator.heading):
                    raise StorageError('document definition differs from candidate')
                edge(cn, 'document', document)
        for c in batches['acs'].candidates:
            mn = metric_nodes[c.metric_code]
            m = mn.payload
            if (c.metric_label != m['label'] or c.measurement.unit != m['unit'] or
                    c.measurement.universe != m['universe'] or c.aggregation != m['aggregation'] or
                    c.measurement.reference_period != m['reference_period'] or
                    c.measurement.geography_vintage != m['publication_vintage'] or
                    c.locator.fields != tuple(m[k] for k in ('estimate', 'margin_of_error',
                                                           'estimate_annotation', 'margin_of_error_annotation')) or
                    c.confidence_level != '90%' or m['uncertainty'] != 'published 90 percent margin of error'):
                raise StorageError('metric definition differs from candidate')
            cn = nodes['candidate', c.fingerprint]
            edge(cn, 'metric', mn)
            edge(cn, 'geography', boundary_nodes[c.measurement.geography_id])
        candidate_bytes = _json(report.content.model_dump(mode='json')).encode()
        candidate_sha = _sha(candidate_bytes)
        if self.staging.objects.read(candidate_sha) != candidate_bytes:
            raise StorageError('retained candidate report differs')
        selection = ReleaseSelection(run_id=report.content.run_id,
            import_ids=tuple(sorted(i['import_id'] for i in imports)),
            candidate_report_id=report.report_id,
            version_ids=tuple(sorted(c.fingerprint for c in candidates)))
        node('query', 'first-slice-selection/1', {'operation': 'one explicit accepted import per source; full ordered membership; no latest; no activation or default read',
            'selection': selection.model_dump(mode='json'), 'imports': sorted(imports, key=lambda i: i['import_id']),
            'candidate_report_sha256': candidate_sha,
            'implementation': {m: files['src/chesterfield_twin/' + m]['sha256'] for m in
                               ('storage/staging.py', 'storage/validation.py', 'storage/releases.py')}})
        node('config', 'first-slice-config/1', {'county': '51041', 'state': '51',
            'tract_definition': '2020 Census tracts', 'boundary_vintage': '2023',
            'source_crs': 'EPSG:4269', 'acs_period': '2019-2023', 'acs_vintage': '2023',
            'document_period': 'FY2025', 'document_localities': ['51041', '51570'],
            'synthetic': report.content.synthetic, 'selection': selection.model_dump(mode='json'),
            'transforms': sorted(t.key for t in transforms.values()),
            'validators': ['candidate-set/1+validate-slice/1', 'first-slice-closure/1'],
            'policy': 'automated validation only; no activation',
            'implementation': {m: files['src/chesterfield_twin/' + m]['sha256'] for m in
                               ('sources/validation.py', 'domain/releases.py')}})
        node('code', 'checkout', snapshot)
        for name in ('uv.lock', 'frontend/package-lock.json'):
            node('dependency', name, files[name])
        node('dependency', 'runtime', runtime)
        ledger = [dict(r) for r in db.execute('SELECT * FROM schema_migration ORDER BY migration_id')]
        for entry in ledger:
            f = files['src/chesterfield_twin/storage/migrations/baseline/' + entry['migration_id']]
            if f['sha256'] != entry['checksum']:
                raise StorageError('snapshot migrations disagree with database ledger')
        node('schema', 'baseline', {'migrations': ledger})
        node('coverage', 'first-slice', {'counts': {'observation': 225, 'boundary': 75, 'document_excerpt': 3},
            'metrics': sorted(metric_nodes), 'geoids': sorted(boundary_nodes),
            'periods': ['2019-2023', '2023', 'FY2025'],
            'uncertainty': 'published 90 percent margin of error; unknown is not zero',
            'boundary_limitation': specs['boundary']['limitations'],
            'document_caveat': ds['scope_caveat'],
            'retention': {s: batches[s].candidates[0].provenance.retention for s in sorted(batches)},
            'acceptance': 'automated validation only; no human interpretation, merge, map, export, active read or UI acceptance'})
        return ReleaseContent(synthetic=report.content.synthetic, selection=selection,
            nodes=tuple(sorted(nodes.values(), key=lambda n: n.node_id)),
            edges=tuple(ReleaseEdge(from_node=a, role=r, to_node=b) for a, r, b in sorted(edges)))

    def _persist_report(self, db, report):
        encoded = _json(report.content.model_dump(mode='json'))
        sha = self.staging.objects.put(encoded.encode())
        if self.staging.objects.read(sha) != encoded.encode():
            raise StorageError('build report object readback failed')
        self._register(db, sha, len(encoded.encode()), 'application/json')
        db.execute('INSERT OR IGNORE INTO release_build_report VALUES (?,?,?,?,?,?,?)',
                   (report.report_id, report.content.run_id, report.content.candidate_report_id,
                    report.content.content_id, int(report.content.valid), encoded, sha))
        row = db.execute('SELECT content_json,object_sha256 FROM release_build_report WHERE report_id=?',
                         (report.report_id,)).fetchone()
        if tuple(row) != (encoded, sha):
            raise StorageError('build report registration conflicts')

    @staticmethod
    def _register(db, sha, length, media):
        db.execute('INSERT OR IGNORE INTO artifact(artifact_id,sha256,byte_length,media_type) VALUES (?,?,?,?)',
                   (sha, sha, length, media))
        row = db.execute('SELECT byte_length FROM artifact WHERE sha256=?', (sha,)).fetchone()
        if row[0] != length:
            raise StorageError('artifact length conflicts')

    def build(self, run_id: str, import_ids: tuple[str, ...], *, expected_report_id: str) -> ReleaseBuildResult:
        if not isinstance(expected_report_id, str) or not re.fullmatch('[0-9a-f]{64}', expected_report_id):
            raise StorageError('explicit expected candidate report identity is required')
        report = CandidateValidation(self.staging.root).validate(run_id, import_ids)
        failure = None
        if report.report_id != expected_report_id:
            failure = 'current candidate report differs from expected report'
        elif not report.content.valid:
            failure = 'current candidate validation failed'
        try:
            if failure:
                raise ValueError(failure)
            with self.staging._locked(), self.staging._connect() as preflight:
                for previous in preflight.execute(
                        "SELECT r.release_id,r.manifest_json FROM release r JOIN release_closure c USING(release_id) WHERE r.status='sealed' AND c.run_id=? AND c.candidate_report_id=?",
                        (run_id, report.report_id)).fetchall():
                    old = ReleaseManifest.model_validate_json(previous['manifest_json'])
                    if old.content.selection.import_ids == tuple(sorted(import_ids)):
                        self._read(preflight, previous['release_id'], verify_current=True)
                snapshot, runtime = self._snapshot(), self._runtime()
            with self.staging._locked(), self.staging._connect(write=True) as db, db:
                db.execute('BEGIN IMMEDIATE')
                candidate_bytes = _json(report.content.model_dump(mode='json')).encode()
                candidate_sha = self.staging.objects.put(candidate_bytes)
                self._register(db, candidate_sha, len(candidate_bytes), 'application/json')
                content = self._closure(db, report, snapshot, runtime)
                rc = ReleaseReportContent(run_id=run_id, import_ids=content.selection.import_ids,
                    synthetic=content.synthetic, candidate_report_id=report.report_id,
                    content_id=content.content_id, issues=report.content.issues)
                build_report = ReleaseBuildReport(report_id=digest(rc.model_dump(mode='json')), content=rc)
                manifest = ReleaseManifest(content=content, report_id=build_report.report_id)
                encoded = _json(manifest.model_dump(mode='json'))
                sha = self.staging.objects.put(encoded.encode())
                if self.staging.objects.read(sha) != encoded.encode():
                    raise StorageError('manifest object readback failed')
                self._persist_report(db, build_report)
                self._register(db, sha, len(encoded.encode()), 'application/json')
                # Final filesystem checks and reconstruction occur before SQL sealing.
                if self._snapshot(retain=False) != snapshot or self._closure(db, report, snapshot, runtime) != content:
                    raise StorageError('build inputs changed before sealing')
                report_bytes = _json(build_report.content.model_dump(mode='json')).encode()
                report_sha = _sha(report_bytes)
                self._artifact(db, report_sha, len(report_bytes))
                self._artifact(db, sha, len(encoded.encode()))
                self._artifact(db, _sha(candidate_bytes), len(candidate_bytes))
                if self.staging.objects.read(report_sha) != report_bytes:
                    raise StorageError('build report changed before SQL sealing')
                if self.staging.objects.read(sha) != encoded.encode():
                    raise StorageError('manifest changed before SQL sealing')
                candidate_sha = _sha(candidate_bytes)
                if self.staging.objects.read(candidate_sha) != candidate_bytes:
                    raise StorageError('candidate report changed before SQL sealing')
                existing = db.execute('SELECT status,manifest_json FROM release WHERE release_id=?',
                                      (manifest.release_id,)).fetchone()
                if existing:
                    if tuple(existing) != ('sealed', encoded):
                        raise StorageError('existing release conflicts')
                    self._read(db, manifest.release_id, verify_current=True)
                else:
                    db.execute("INSERT INTO release VALUES (?,'draft',?,NULL)", (manifest.release_id, encoded))
                    db.executemany('INSERT INTO release_import VALUES (?,?)',
                                   [(manifest.release_id, i) for i in content.selection.import_ids])
                    db.executemany('INSERT INTO release_version VALUES (?,?)',
                                   [(manifest.release_id, v) for v in content.selection.version_ids])
                    db.executemany('INSERT INTO release_dependency VALUES (?,?,?,?,?)',
                        [(manifest.release_id, n.node_id, n.kind, n.key, _json(n.model_dump(mode='json'))) for n in content.nodes])
                    db.executemany('INSERT INTO release_edge VALUES (?,?,?,?)',
                        [(manifest.release_id, e.from_node, e.role, e.to_node) for e in content.edges])
                    db.execute('INSERT INTO release_closure VALUES (?,?,?,?,?,?)',
                        (manifest.release_id, run_id, report.report_id, build_report.report_id, sha, content.content_id))
                    db.execute("UPDATE release SET status='sealed', sealed_at=CURRENT_TIMESTAMP WHERE release_id=?",
                               (manifest.release_id,))
                return ReleaseBuildResult(report=build_report, manifest=manifest, sealed=True)
        except (StorageError, OSError, ValueError, KeyError, TypeError, ValidationError, sqlite3.Error):
            rc = ReleaseReportContent(run_id=run_id, import_ids=tuple(sorted(import_ids)),
                synthetic=report.content.synthetic, candidate_report_id=report.report_id,
                issues=(ReportIssue(code='closure_integrity', message='Selected evidence or reproducibility dependencies failed closure verification'),))
            failed = ReleaseBuildReport(report_id=digest(rc.model_dump(mode='json')), content=rc)
            with self.staging._locked(), self.staging._connect(write=True) as db, db:
                self._persist_report(db, failed)
            return ReleaseBuildResult(report=failed)

    @staticmethod
    def _artifact(db, sha, length):
        row = db.execute('SELECT artifact_id,sha256,byte_length,media_type FROM artifact WHERE sha256=?', (sha,)).fetchone()
        if row is None or tuple(row) != (sha, sha, length, 'application/json'):
            raise StorageError('report or manifest artifact registration differs')

    def _read(self, db, release_id, *, verify_current):
        row = db.execute('SELECT * FROM release WHERE release_id=?', (release_id,)).fetchone()
        if row is None or row['status'] != 'sealed':
            raise StorageError('unknown sealed release')
        manifest = ReleaseManifest.model_validate_json(row['manifest_json'])
        encoded = _json(manifest.model_dump(mode='json'))
        if manifest.release_id != release_id or encoded != row['manifest_json']:
            raise StorageError('manifest identity is invalid')
        content, selection = manifest.content, manifest.content.selection
        closure = db.execute('SELECT * FROM release_closure WHERE release_id=?', (release_id,)).fetchone()
        if closure is None or tuple(closure) != (release_id, selection.run_id, selection.candidate_report_id,
                                                manifest.report_id, _sha(encoded.encode()), content.content_id):
            raise StorageError('closure binding differs')
        self._artifact(db, closure['manifest_sha256'], len(encoded.encode()))
        if self.staging.objects.read(closure['manifest_sha256']) != encoded.encode():
            raise StorageError('retained manifest differs')
        br = db.execute('SELECT * FROM release_build_report WHERE report_id=?', (manifest.report_id,)).fetchone()
        if br is None:
            raise StorageError('missing build report')
        rc = ReleaseReportContent.model_validate_json(br['content_json'])
        report_encoded = _json(rc.model_dump(mode='json'))
        self._artifact(db, br['object_sha256'], len(report_encoded.encode()))
        if (br['run_id'] != rc.run_id or br['candidate_report_id'] != rc.candidate_report_id or
                br['content_id'] != rc.content_id or br['content_json'] != report_encoded or
                br['object_sha256'] != _sha(report_encoded.encode())):
            raise StorageError('build report SQL metadata differs')
        if (digest(rc.model_dump(mode='json')) != manifest.report_id or not rc.valid or
                rc.content_id != content.content_id or rc.run_id != selection.run_id or
                rc.import_ids != selection.import_ids or rc.candidate_report_id != selection.candidate_report_id or
                rc.synthetic != content.synthetic or br['valid'] != 1 or
                self.staging.objects.read(br['object_sha256']) != _json(rc.model_dump(mode='json')).encode()):
            raise StorageError('build report binding differs')
        for table, column, expected in (
                ('release_import', 'import_id', selection.import_ids),
                ('release_version', 'version_id', selection.version_ids)):
            actual = tuple(r[0] for r in db.execute(f'SELECT {column} FROM {table} WHERE release_id=? ORDER BY {column}', (release_id,)))
            if actual != expected:
                raise StorageError('SQL selection membership differs')
        actual_nodes = tuple(tuple(r) for r in db.execute('SELECT node_id,kind,node_key,node_json FROM release_dependency WHERE release_id=? ORDER BY node_id', (release_id,)))
        if actual_nodes != tuple((n.node_id, n.kind, n.key, _json(n.model_dump(mode='json'))) for n in content.nodes):
            raise StorageError('SQL node membership differs')
        actual_edges = tuple(tuple(r) for r in db.execute('SELECT from_node,role,to_node FROM release_edge WHERE release_id=? ORDER BY from_node,role,to_node', (release_id,)))
        if actual_edges != tuple((e.from_node, e.role, e.to_node) for e in content.edges):
            raise StorageError('SQL edge membership differs')
        nodes = {(n.kind, n.key): n for n in content.nodes}
        cp = db.execute('SELECT content_json FROM candidate_validation_report WHERE report_id=? AND run_id=?',
                        (selection.candidate_report_id, selection.run_id)).fetchone()
        if cp is None or digest(json.loads(cp[0])) != selection.candidate_report_id:
            raise StorageError('candidate report identity differs')
        q = nodes['query', 'first-slice-selection/1'].payload
        self._artifact(db, q['candidate_report_sha256'], len(cp[0].encode()))
        if self.staging.objects.read(q['candidate_report_sha256']) != cp[0].encode():
            raise StorageError('candidate report object differs')
        if verify_current:
            from chesterfield_twin.domain.validation_reports import ReportContent, ValidationReport
            report = ValidationReport(report_id=selection.candidate_report_id,
                                      content=ReportContent.model_validate_json(cp[0]))
            rebuilt = self._closure(db, report, nodes['code', 'checkout'].payload,
                                    nodes['dependency', 'runtime'].payload)
            if rebuilt != content:
                raise StorageError('current closure differs from sealed manifest')
        return manifest

    def read_release(self, release_id: str, *, verify_current: bool = True) -> ReleaseManifest:
        """Default verifies retained dependencies; False is historical metadata only."""
        with self.staging._locked(), self.staging._connect() as db:
            try:
                return self._read(db, release_id, verify_current=verify_current)
            except (OSError, ValueError, KeyError, TypeError, ValidationError, sqlite3.Error) as exc:
                raise StorageError('sealed release verification failed') from exc
