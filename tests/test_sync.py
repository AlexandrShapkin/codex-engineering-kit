"""Offline bundle/sync safety and lifecycle regression tests."""
import copy
from contextlib import redirect_stdout, redirect_stderr
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

from engineering_kit.sync import (LOCK, PROFILES, SOURCES, SyncError, digest,
                                  encoded, export, load, plan, write)
from engineering_kit.cli import main


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / 'consumer'
        self.root.mkdir()
        self.bundle = self.base / 'bundle.json'
        self.name = '.engineering-kit/reference.md'
        self.obj = {'manifest': {'format': 1, 'upstream': 'a' * 40,
                                'profile': 'minimal', 'files': {}}, 'contents': {}}
        self.save({'%s' % self.name: 'one\n'})

    def save(self, contents=None):
        if contents is not None:
            self.obj['contents'] = contents
            self.obj['manifest']['files'] = {n: digest(v.encode()) for n, v in contents.items()}
        self.bundle.write_bytes(encoded(self.obj))

    def apply(self):
        result, _ = plan(self.root, self.bundle)
        return write(self.root, self.bundle, [c['path'] for c in result['changes']],
                     result['plan_sha256'])

    def test_install_update_rollback_preserves_rules(self):
        for name in ('AGENTS.md', 'rules.md', '.github/workflows/native.yml'):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('native')
        before = sorted(str(p.relative_to(self.root)) for p in self.root.rglob('*'))
        first, _ = plan(self.root, self.bundle)
        self.assertEqual(before, sorted(str(p.relative_to(self.root)) for p in self.root.rglob('*')))
        self.apply()
        self.assertEqual(plan(self.root, self.bundle)[0]['changes'], [])
        self.save({self.name: 'two\n', '.engineering-kit/new.md': 'new'})
        self.apply()
        self.save({self.name: 'one\n'})
        self.apply()
        self.assertFalse((self.root / '.engineering-kit/new.md').exists())
        for name in ('AGENTS.md', 'rules.md', '.github/workflows/native.yml'):
            self.assertEqual((self.root / name).read_text(), 'native')
        self.assertEqual(first['upstream'], 'a' * 40)

    def test_exact_authorization_and_stale_plan(self):
        result, _ = plan(self.root, self.bundle)
        for allowed, token in (([], result['plan_sha256']),
                               ([self.name, LOCK, 'AGENTS.md'], result['plan_sha256']),
                               ([self.name, LOCK], 'bad')):
            with self.assertRaises(SyncError):
                write(self.root, self.bundle, allowed, token)
            self.assertEqual(list(self.root.iterdir()), [])
        self.save({self.name: 'changed'})
        with self.assertRaises(SyncError):
            write(self.root, self.bundle, [self.name, LOCK], result['plan_sha256'])

    def test_plan_token_is_bound_to_consumer_directory(self):
        other = self.base / 'other'
        other.mkdir()
        for installed in (False, True):
            if installed:
                self.apply()
                for path in self.root.rglob('*'):
                    target = other / path.relative_to(self.root)
                    if path.is_dir():
                        target.mkdir(exist_ok=True)
                    else:
                        target.write_bytes(path.read_bytes())
                self.save({self.name: 'updated'})
            a, _ = plan(self.root, self.bundle)
            b, _ = plan(other, self.bundle)
            self.assertEqual(a['changes'], b['changes'])
            self.assertNotEqual(a['plan_sha256'], b['plan_sha256'])
            before = {str(p): p.read_bytes() for p in other.rglob('*') if p.is_file()}
            with self.assertRaises(SyncError):
                write(other, self.bundle, [c['path'] for c in a['changes']],
                      a['plan_sha256'])
            self.assertEqual(before, {str(p): p.read_bytes()
                                      for p in other.rglob('*') if p.is_file()})
            self.assertEqual(plan(self.root / '.', self.bundle)[0]['plan_sha256'],
                             a['plan_sha256'])

    def test_replaced_consumer_directory_invalidates_plan(self):
        result, _ = plan(self.root, self.bundle)
        self.root.rename(self.base / 'original')
        self.root.mkdir()
        with self.assertRaises(SyncError):
            write(self.root, self.bundle, [c['path'] for c in result['changes']],
                  result['plan_sha256'])
        self.assertEqual(list(self.root.iterdir()), [])

    def test_deep_json_is_controlled_failure_for_bundle_and_lock(self):
        depth = 10000
        deep = b'[' * depth + b'0' + b']' * depth
        for target in (self.bundle, self.root / LOCK):
            self.save({self.name: 'one\n'})
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(deep)
            before = {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
            with self.assertRaises(SyncError):
                plan(self.root, self.bundle)
            for operation in ('plan', 'write'):
                args = ['sync', operation, '--root', str(self.root),
                        '--bundle', str(self.bundle)]
                if operation == 'write':
                    args += ['--plan-sha256', 'bad']
                with redirect_stdout(io.StringIO()) as output, \
                        redirect_stderr(io.StringIO()) as errors:
                    self.assertEqual(main(args), 1)
                result = json.loads(output.getvalue())
                self.assertFalse(result['ok'])
                self.assertIn(result['error'], ('invalid JSON', 'invalid bundle',
                                                'invalid manifest'))
                self.assertEqual(errors.getvalue(), '')
            self.assertEqual(before, {str(p): p.read_bytes()
                                      for p in self.root.rglob('*') if p.is_file()})

    def test_local_edits_missing_collision_and_lock_tampering(self):
        self.apply()
        path = self.root / self.name
        for content in ('local edit', None):
            if content is None:
                path.unlink()
            else:
                path.write_text(content)
            with self.assertRaises(SyncError):
                plan(self.root, self.bundle)
        path.write_text('one\n')
        (self.root / LOCK).write_text('{}')
        with self.assertRaises(SyncError):
            plan(self.root, self.bundle)
        (self.root / LOCK).unlink()
        with self.assertRaises(SyncError):
            plan(self.root, self.bundle)

    def test_invalid_paths_and_hashes(self):
        pristine = copy.deepcopy(self.obj)
        for name in ('../escape', '/absolute', 'AGENTS.md', '.engineering-kit/../escape',
                     '.engineering-kit//x', '.engineering-kit/./x', LOCK,
                     '.engineering-kit/a\\b', '.engineering-kit/x\n', LOCK + '/child'):
            self.obj = copy.deepcopy(pristine)
            self.save({name: 'bad'})
            with self.subTest(name=name), self.assertRaises(SyncError):
                plan(self.root, self.bundle)
        self.obj = pristine
        self.obj['contents'][self.name] = 'tampered'
        self.save()
        with self.assertRaises(SyncError):
            plan(self.root, self.bundle)

    def test_symlinks_and_non_directory_parent(self):
        outside = self.base / 'outside'
        outside.mkdir()
        namespace = self.root / '.engineering-kit'
        namespace.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(SyncError):
            self.apply()
        self.assertEqual(list(outside.iterdir()), [])
        namespace.unlink()
        namespace.mkdir()
        (self.root / self.name).symlink_to(outside / 'missing')
        with self.assertRaises(SyncError):
            self.apply()
        (self.root / self.name).unlink()
        (self.root / LOCK).symlink_to(outside / 'lock')
        with self.assertRaises(SyncError):
            self.apply()
        (self.root / LOCK).unlink()
        namespace.rmdir()
        namespace.write_text('file')
        with self.assertRaises(SyncError):
            plan(self.root, self.bundle)

    def test_bad_schema_duplicate_keys_and_overlap(self):
        for data in (b'{"manifest":{},"manifest":{}}', b'[]', b'null', b'{'):
            self.bundle.write_bytes(data)
            with self.assertRaises(SyncError):
                plan(self.root, self.bundle)
        self.save({'.engineering-kit/a': 'a', '.engineering-kit/a-foo': 'c',
                   '.engineering-kit/a/b': 'b'})
        with self.assertRaises(SyncError):
            plan(self.root, self.bundle)

    def test_export_exact_commit_all_profiles(self):
        source = self.base / 'source'
        source.mkdir()
        def git(*args):
            return subprocess.check_output(['git', '-C', str(source), *args]).decode().strip()
        git('init', '-q')
        for name in (*SOURCES, *('profiles/sync/' + p + '.md' for p in PROFILES)):
            path = source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('committed\n')
        git('add', '.')
        git('-c', 'user.name=Offline Test', '-c', 'user.email=test@example.invalid',
            'commit', '-qm', 'fixture')
        revision = git('rev-parse', 'HEAD')
        (source / SOURCES[0]).write_text('dirty work must not be exported')
        for profile in PROFILES:
            target = self.base / (profile + '.json')
            export(source, revision, profile, target)
            obj = json.loads(target.read_text())
            self.assertEqual(obj['manifest']['upstream'], revision)
            self.assertEqual(obj['contents']['.engineering-kit/' + SOURCES[0]], 'committed\n')
            with self.assertRaises(FileExistsError):
                export(source, revision, profile, target)
        with self.assertRaises(SyncError):
            export(source, revision[:8], 'minimal', self.base / 'bad')
        tracked = source / SOURCES[0]
        tracked.unlink()
        tracked.symlink_to(self.bundle)
        git('add', '.')
        git('-c', 'user.name=Offline Test', '-c', 'user.email=test@example.invalid',
            'commit', '-qm', 'symlink fixture')
        with self.assertRaises(SyncError):
            export(source, git('rev-parse', 'HEAD'), 'minimal', self.base / 'symlink.json')
        self.assertFalse((self.base / 'symlink.json').exists())

    def test_root_and_bundle_symlinks(self):
        alias = self.base / 'alias'
        alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(SyncError):
            plan(alias, self.bundle)
        linked = self.base / 'linked.json'
        linked.symlink_to(self.bundle)
        with self.assertRaises(SyncError):
            plan(self.root, linked)

    def test_manifest_schema_and_oversized_input(self):
        original = copy.deepcopy(self.obj)
        for key, value in (('upstream', 'short'), ('profile', 'unknown'),
                           ('format', True), ('files', [])):
            self.obj = copy.deepcopy(original)
            self.obj['manifest'][key] = value
            self.save()
            with self.subTest(key=key), self.assertRaises(SyncError):
                plan(self.root, self.bundle)
        self.bundle.write_bytes(b' ' * (1024 * 1024 + 1))
        with self.assertRaises(SyncError):
            plan(self.root, self.bundle)

    def test_json_recursion_error_becomes_sync_error(self):
        with mock.patch('engineering_kit.sync.json.loads', side_effect=RecursionError):
            with self.assertRaisesRegex(SyncError, '^invalid JSON$'):
                load(b'[]')

    def test_sync_never_spawns_process_or_network(self):
        with mock.patch('subprocess.Popen', side_effect=AssertionError('process')), \
                mock.patch('socket.socket', side_effect=AssertionError('network')):
            self.apply()
            plan(self.root, self.bundle)

    def test_cli(self):
        self.assertEqual(main(['sync', 'plan', '--root', str(self.root),
                               '--bundle', str(self.bundle)]), 0)
        self.assertEqual(main(['sync', 'write', '--root', str(self.root),
                               '--bundle', str(self.bundle), '--plan-sha256', 'bad']), 1)
