"""Administrative channel uses the existing sync engine with isolated policy."""
import copy
from pathlib import Path
import subprocess
import tempfile
import unittest

from engineering_kit.sync import (ADMIN_LOCK, ADMIN_PATHS, LOCK, SyncError,
                                  digest, encoded, export, plan, write)


class AdminTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / 'consumer'
        self.root.mkdir()
        self.bundle = self.base / 'admin.json'
        self.obj = {'manifest': {'format': 2, 'upstream': 'a' * 40,
                    'profile': 'administrative', 'publication': 'private',
                    'owner': 'AlexandrShapkin/project-template', 'files': {}},
                    'contents': {}}
        self.save({'AGENTS.md': 'shared v1\n'})

    def save(self, contents=None):
        if contents is not None:
            self.obj['contents'] = contents
        self.obj['manifest']['files'] = {
            n: digest(v.encode()) for n, v in self.obj['contents'].items()}
        self.bundle.write_bytes(encoded(self.obj))

    def apply(self):
        result, _ = plan(self.root, self.bundle, 'admin')
        return write(self.root, self.bundle,
                     [c['path'] for c in result['changes']],
                     result['plan_sha256'], 'admin')

    def test_pilot_upgrade_rollback_and_independent_channels(self):
        local = self.root / 'AGENTS.local.md'
        local.write_text('strong native gate\n')
        kit = self.base / 'kit.json'
        obj = {'manifest': {'format': 1, 'upstream': 'b' * 40,
               'profile': 'minimal', 'files': {}},
               'contents': {'.engineering-kit/PROFILE.md': 'technical reference'}}
        def kit_apply():
            obj['manifest']['files'] = {n: digest(v.encode())
                                       for n, v in obj['contents'].items()}
            kit.write_bytes(encoded(obj))
            p, _ = plan(self.root, kit)
            write(self.root, kit, [c['path'] for c in p['changes']], p['plan_sha256'])
        kit_apply()
        kit_lock = (self.root / LOCK).read_bytes()
        before = sorted(self.root.rglob('*'))
        plan(self.root, self.bundle, 'admin')
        self.assertEqual(before, sorted(self.root.rglob('*')))
        self.apply()
        original = copy.deepcopy(self.obj)
        self.assertEqual(plan(self.root, self.bundle, 'admin')[0]['changes'], [])
        self.obj['manifest']['upstream'] = 'c' * 40
        self.save({'AGENTS.md': 'shared v2\n', 'docs/WORKFLOW.md': 'navigation'})
        self.apply()
        self.assertEqual((self.root / LOCK).read_bytes(), kit_lock)
        admin_lock = (self.root / ADMIN_LOCK).read_bytes()
        obj['manifest']['upstream'] = 'd' * 40
        kit_apply()
        self.assertEqual((self.root / ADMIN_LOCK).read_bytes(), admin_lock)
        self.obj = original
        self.save()
        p, _ = plan(self.root, self.bundle, 'admin')
        self.assertIn({'path': 'docs/WORKFLOW.md', 'action': 'delete'}, p['changes'])
        with self.assertRaises(SyncError):
            write(self.root, self.bundle, ['AGENTS.md', ADMIN_LOCK], p['plan_sha256'], 'admin')
        self.apply()
        self.assertEqual(local.read_text(), 'strong native gate\n')
        self.assertEqual((self.root / 'AGENTS.md').read_text(), 'shared v1\n')
        self.assertFalse((self.root / 'docs/WORKFLOW.md').exists())

    def test_drift_missing_collision_symlink(self):
        path = self.root / 'AGENTS.md'
        path.write_text('user work')
        with self.assertRaises(SyncError):
            self.apply()
        path.unlink()
        self.apply()
        path.write_text('local edit')
        with self.assertRaises(SyncError):
            self.apply()
        path.unlink()
        with self.assertRaises(SyncError):
            self.apply()
        path.symlink_to(self.base / 'absent')
        with self.assertRaises(SyncError):
            self.apply()

    def test_paths_classification_and_channel_separation(self):
        original = copy.deepcopy(self.obj)
        for name in ('../AGENTS.md', '/AGENTS.md', 'docs/../AGENTS.md',
                     'AGENTS.local.md', '.github/workflows/native.yml',
                     ADMIN_LOCK, '.engineering-kit/PROFILE.md'):
            self.save({name: 'bad'})
            with self.assertRaises(SyncError):
                self.apply()
        self.obj = original
        for key, value in (('publication', 'public'), ('owner', 'other'),
                           ('format', 1), ('profile', 'minimal')):
            self.obj = copy.deepcopy(original)
            self.obj['manifest'][key] = value
            self.save()
            with self.assertRaises(SyncError):
                self.apply()
        self.obj = original
        self.save()
        with self.assertRaises(SyncError):
            plan(self.root, self.bundle)
        p, _ = plan(self.root, self.bundle, 'admin')
        with self.assertRaises(SyncError):
            write(self.root, self.bundle, [], p['plan_sha256'], 'admin')
        path = self.root / 'AGENTS.md'
        path.write_text('intervening edit')
        with self.assertRaises(SyncError):
            write(self.root, self.bundle, ['AGENTS.md', ADMIN_LOCK], p['plan_sha256'], 'admin')
        self.assertEqual(path.read_text(), 'intervening edit')

    def test_export_from_exact_commit_not_worktree(self):
        source = self.base / 'source'
        source.mkdir()
        def git(*args):
            return subprocess.check_output(['git', '-C', str(source), *args]).decode().strip()
        git('init', '-q')
        for name in ADMIN_PATHS:
            path = source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('reviewed')
        git('add', '.')
        git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
            '-c', 'core.hooksPath=/dev/null', 'commit', '-qm', 'fixture')
        revision = git('rev-parse', 'HEAD')
        (source / 'AGENTS.md').write_text('unreviewed')
        output = self.base / 'export.json'
        result = export(source, revision, 'administrative', output, 'admin')
        self.assertEqual(result['upstream'], revision)
        self.assertEqual(result['publication'], 'private')
        p, contents = plan(self.root, output, 'admin')
        self.assertEqual(contents['AGENTS.md'], b'reviewed')
        (source / 'AGENTS.md').unlink()
        (source / 'AGENTS.md').symlink_to('other')
        git('add', 'AGENTS.md')
        git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
            '-c', 'core.hooksPath=/dev/null', 'commit', '-qm', 'symlink')
        with self.assertRaises(SyncError):
            export(source, git('rev-parse', 'HEAD'), 'administrative',
                   self.base / 'unsafe.json', 'admin')
