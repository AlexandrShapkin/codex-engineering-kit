"""Two independent canonical sources; disposable source update/rollback cycle."""
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from engineering_kit.source_update import (owner, plan_source, record_path,
                                          source_map, write_source)
from engineering_kit.sync import (SyncError, digest, encoded, export, plan,
                                 channel_lock)


class SourceUpdateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / 'consumer'
        self.root.mkdir()
        self.sources = {}
        self.pins = {}
        for channel in ('kit', 'admin'):
            source = self.base / channel
            source.mkdir()
            self.sources[channel] = source
            self.git(channel, 'init', '-q')
            for name in (*source_map(channel).values(), 'LICENSE'):
                path = source / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('reviewed ' + name + '\n')
            first = self.commit(channel)
            contents = {}
            for name, path in source_map(channel).items():
                data = (source / path).read_bytes()
                destination = self.root / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(data)
                contents[name] = {'source_path': path, 'sha256': digest(data)}
            record = {'method': 'reviewed-public-source-migration',
                      'repository': owner(channel), 'revision': first,
                      'license_at': first, 'files': contents}
            (self.root / record_path(channel)).write_bytes(encoded(record))
            changed = source / next(iter(sorted(source_map(channel).values())))
            changed.write_text('reviewed upstream update\n')
            self.pins[channel] = (first, self.commit(channel))
        (self.root / 'AGENTS.local.md').write_text('stronger product security gate\n')
        native = self.root / '.github/workflows/native.yml'
        native.parent.mkdir(parents=True, exist_ok=True)
        native.write_text('mandatory native CI\n')

    def git(self, channel, *args):
        return subprocess.check_output(['git', '-C', str(self.sources[channel]),
                                       *args]).decode().strip()

    def commit(self, channel):
        self.git(channel, 'add', '.')
        self.git(channel, '-c', 'user.name=Fixture', '-c', 'user.email=test@example.invalid',
                 '-c', 'core.hooksPath=/dev/null', 'commit', '-qm', 'fixture')
        return self.git(channel, 'rev-parse', 'HEAD')

    def proposal(self, channel='admin', pin=None, root=None):
        return plan_source(root or self.root, self.sources[channel],
                           pin or self.pins[channel][1], channel)

    def apply(self, channel, pin):
        p, _ = self.proposal(channel, pin)
        return write_source(self.root, self.sources[channel], pin, channel,
                            [c['path'] for c in p['changes']], p['plan_sha256'])

    def snapshot(self):
        return {str(p.relative_to(self.root)): p.read_bytes()
                for p in self.root.rglob('*') if p.is_file()}

    def test_full_cycle_determinism_independence_and_rollback(self):
        before = self.snapshot()
        p, contents = self.proposal()
        self.assertEqual(p, self.proposal()[0])
        self.assertEqual(before, self.snapshot())
        self.assertEqual(set(p['diffs']), {c['path'] for c in p['changes']})
        self.apply('admin', self.pins['admin'][1])
        self.assertEqual(self.proposal()[0]['changes'], [])
        for name in source_map('kit'):
            self.assertEqual((self.root / name).read_bytes(), before[name])
        admin = {n: (self.root / n).read_bytes()
                 for n in (*source_map('admin'), record_path('admin'))}
        self.apply('kit', self.pins['kit'][1])
        for n, data in admin.items():
            self.assertEqual((self.root / n).read_bytes(), data)
        for channel in ('admin', 'kit'):
            self.apply(channel, self.pins[channel][0])
        self.assertEqual(self.snapshot(), before)

    def test_exact_permissions_stale_plan_cross_root_and_changed_revision(self):
        p, _ = self.proposal()
        for allow, token in (([], p['plan_sha256']),
                             ([c['path'] for c in p['changes']], '0' * 64),
                             ([c['path'] for c in p['changes']] + ['AGENTS.local.md'],
                              p['plan_sha256'])):
            with self.assertRaises(SyncError):
                write_source(self.root, self.sources['admin'], self.pins['admin'][1],
                             'admin', allow, token)
        other = self.base / 'other'
        import shutil
        shutil.copytree(self.root, other)
        self.assertNotEqual(p['plan_sha256'], self.proposal(root=other)[0]['plan_sha256'])
        with self.assertRaises(SyncError):
            write_source(self.root, self.sources['admin'], self.pins['admin'][0], 'admin',
                         [c['path'] for c in p['changes']], p['plan_sha256'])
        (self.root / 'AGENTS.md').write_text('intervening edit')
        with self.assertRaises(SyncError):
            self.proposal()

    def test_text_diffs_show_pinned_content_and_record_without_writes(self):
        before = self.snapshot()
        # An uncommitted upstream edit must never enter the pinned proposal.
        changed = next(iter(sorted(source_map('admin').values())))
        (self.sources['admin'] / changed).write_text('unreviewed worktree edit\n')
        p, contents = self.proposal()
        self.assertEqual(set(p['text_diffs']), set(p['diffs']))
        diff = p['text_diffs'][changed]
        self.assertIn('-reviewed ' + changed + '\n', diff)
        self.assertIn('+reviewed upstream update\n', diff)
        self.assertNotIn('unreviewed worktree edit', diff)
        record_diff = p['text_diffs'][record_path('admin')]
        self.assertIn(self.pins['admin'][0], record_diff)
        self.assertIn(self.pins['admin'][1], record_diff)
        self.assertEqual(before, self.snapshot())
        self.apply('admin', self.pins['admin'][1])
        self.assertEqual(self.proposal()[0]['text_diffs'], {})

    def test_bad_records_and_unmanaged_adoption(self):
        path = self.root / record_path('admin')
        original = json.loads(path.read_bytes())
        cases = []
        for key, value in (('revision', 'main'), ('repository', owner('kit')),
                           ('license_at', 'bad'), ('method', 'approved-bundle')):
            obj = copy.deepcopy(original)
            obj[key] = value
            cases.append(obj)
        for name in ('../escape', 'AGENTS.local.md', '.github/workflows/native.yml'):
            obj = copy.deepcopy(original)
            obj['files'][name] = obj['files'].pop('AGENTS.md')
            cases.append(obj)
        obj = copy.deepcopy(original)
        obj['files']['AGENTS.md']['source_path'] = '../escape'
        cases.append(obj)
        obj = copy.deepcopy(original)
        obj['files']['AGENTS.md']['sha256'] = '0' * 64
        cases.append(obj)
        before = self.snapshot()
        for obj in cases:
            path.write_bytes(encoded(obj))
            with self.assertRaises(SyncError):
                self.proposal()
        path.write_bytes(b'{"revision":1,"revision":2}')
        with self.assertRaises(SyncError):
            self.proposal()
        path.unlink()
        with self.assertRaises(SyncError):
            self.proposal()
        self.assertEqual((self.root / 'AGENTS.md').read_bytes(), before['AGENTS.md'])

    def test_missing_symlinks_and_bundle_protocol_remain_closed(self):
        path = self.root / 'AGENTS.md'
        data = path.read_bytes()
        path.unlink()
        with self.assertRaises(SyncError):
            self.proposal()
        path.symlink_to(self.base / 'absent')
        with self.assertRaises(SyncError):
            self.proposal()
        path.unlink()
        path.write_bytes(data)
        alias = self.base / 'alias'
        alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(SyncError):
            self.proposal(root=alias)
        alias.unlink()
        source_alias = self.base / 'source-alias'
        source_alias.symlink_to(self.sources['admin'], target_is_directory=True)
        with self.assertRaises(SyncError):
            plan_source(self.root, source_alias, self.pins['admin'][1], 'admin')
        bundle = self.base / 'private.json'
        export(self.sources['admin'], self.pins['admin'][1], 'administrative', bundle, 'admin')
        with self.assertRaises(SyncError):
            plan(self.root, bundle, 'admin')  # still unmanaged; no fabricated lock
        (self.root / channel_lock('admin')).write_text('{}')
        with self.assertRaises(SyncError):
            self.proposal()

    def test_committed_blobs_only_and_unsafe_source_and_license_change(self):
        (self.sources['admin'] / 'AGENTS.md').write_text('uncommitted data')
        p, contents = self.proposal()
        self.assertEqual(contents['AGENTS.md'], self.git('admin', 'show',
                         self.pins['admin'][1] + ':AGENTS.md').encode() + b'\n')
        with self.assertRaises(SyncError):
            self.proposal(pin='main')
        (self.sources['admin'] / 'LICENSE').write_text('changed rights')
        bad = self.commit('admin')
        with self.assertRaises(SyncError):
            self.proposal(pin=bad)
        (self.sources['admin'] / 'LICENSE').write_text('reviewed LICENSE\n')
        agent = self.sources['admin'] / 'AGENTS.md'
        agent.unlink()
        agent.symlink_to('other')
        bad = self.commit('admin')
        with self.assertRaises(SyncError):
            self.proposal(pin=bad)

    def test_cli_plan_and_refusal(self):
        from engineering_kit.cli import main
        from contextlib import redirect_stdout
        from io import StringIO
        args = ['source-update', 'plan', '--root', str(self.root), '--source',
                str(self.sources['admin']), '--channel', 'admin', '--revision',
                self.pins['admin'][1]]
        with redirect_stdout(StringIO()) as output:
            self.assertEqual(main(args), 0)
        self.assertTrue(json.loads(output.getvalue())['ok'])
        args[1] = 'write'
        with redirect_stdout(StringIO()):
            self.assertEqual(main(args + ['--plan-sha256', '0' * 64]), 1)

    def test_partial_io_failure_snapshot_recovery(self):
        from unittest.mock import patch
        import os
        before = self.snapshot()
        replace = os.replace
        calls = []

        def fail_record(src, dst):
            calls.append(str(dst))
            if str(dst).endswith('source.json'):
                raise OSError('injected record replacement failure')
            return replace(src, dst)

        with patch('engineering_kit.sync.os.replace', side_effect=fail_record):
            with self.assertRaises(OSError):
                self.apply('admin', self.pins['admin'][1])
        self.assertGreater(len(calls), 1)
        self.assertNotEqual(self.snapshot(), before)
        with self.assertRaises(SyncError):
            self.proposal()
        # Operator restores the verified pre-write snapshot, never deletes locks
        # or silently overwrites drift. In fixtures this dictionary is that backup.
        for name, data in before.items():
            (self.root / name).write_bytes(data)
        self.assertEqual(self.snapshot(), before)

        self.apply('admin', self.pins['admin'][1])
        self.apply('admin', self.pins['admin'][0])
        self.assertEqual(self.snapshot(), before)

    def test_historical_prelicense_rollback_matches_licensing_payload(self):
        # Existing installations pin pre-LICENSE source but retain a separately
        # approved later license identity. Rollback must retain that boundary.
        source = self.sources['admin']
        (source / 'LICENSE').unlink()
        historical = self.commit('admin')
        (source / 'LICENSE').write_text('reviewed LICENSE\n')
        licensed = self.commit('admin')
        self.apply('admin', licensed)
        record = self.root / record_path('admin')
        obj = json.loads(record.read_bytes())
        obj['license_at'] = licensed
        record.write_bytes(encoded(obj))
        self.apply('admin', historical)
        self.assertEqual(json.loads(record.read_bytes())['revision'], historical)
        (source / 'AGENTS.md').write_text('different unlicensed bytes')
        (source / 'LICENSE').unlink()
        changed_unlicensed = self.commit('admin')
        with self.assertRaises(SyncError):
            self.proposal(pin=changed_unlicensed)
