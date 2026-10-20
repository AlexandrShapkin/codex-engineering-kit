"""Public protocol isolation; synthetic source bytes, never publication approval."""
import copy
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

from engineering_kit.distribution import generate
from engineering_kit.cli import main
from engineering_kit.sync import (ADMIN_LOCK, ADMIN_PATHS, LOCK, PREFIX, SOURCES,
                                  SyncError, digest, encoded, export, plan, write)


class DistributionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.source = self.base / 'source'
        self.source.mkdir()
        self.root = self.base / 'rustcraft-fixture'
        self.root.mkdir()
        self.git('init', '-q')
        for name in (*SOURCES, 'profiles/sync/minimal.md', *ADMIN_PATHS):
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('Synthetic reviewed reference: ' + name + '\n')
        self.revision = self.commit()

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.source), *args]).decode().strip()

    def commit(self):
        self.git('add', '.')
        self.git('-c', 'user.name=Offline Fixture', '-c', 'user.email=test@example.invalid',
                 'commit', '-qm', 'synthetic source')
        return self.git('rev-parse', 'HEAD')

    def candidate(self, channel='kit', suffix=''):
        profile = 'administrative' if channel == 'admin' else 'minimal'
        private = self.base / (channel + suffix + '-private.json')
        export(self.source, self.revision, profile, private, channel)
        original = json.loads(private.read_bytes())['manifest']
        review = self.base / (channel + suffix + '-review.json')
        review.write_bytes(encoded({'format': 1, 'channel': channel,
                                   'upstream': self.revision,
                                   'files': {n: {'sha256': h, 'classification': 'PUBLIC-SAFE'}
                                             for n, h in original['files'].items()}}))
        output = self.base / (channel + suffix + '-public.json')
        result = generate(self.source, self.revision, profile, output, channel,
                          review, digest(review.read_bytes()), 'f' * 40)
        self.assertFalse(result['publication_authorized'])
        return output, digest(output.read_bytes()), review

    def apply(self, bundle, pin, channel='kit'):
        p, _ = plan(self.root, bundle, channel, pin)
        write(self.root, bundle, [c['path'] for c in p['changes']],
              p['plan_sha256'], channel, pin)

    def test_reproducible_committed_bytes_and_review_gate(self):
        first, pin, review = self.candidate()
        (self.source / SOURCES[0]).write_text('uncommitted content')
        second, other_pin, _ = self.candidate(suffix='repeat')
        self.assertEqual(first.read_bytes(), second.read_bytes())
        self.assertEqual(pin, other_pin)
        audit = json.loads(review.read_bytes())
        for classification in ('REDACT/REFACTOR', 'BLOCKED', 'public-safe'):
            audit['files'][PREFIX + SOURCES[0]]['classification'] = classification
            review.write_bytes(encoded(audit))
            with self.assertRaises(SyncError):
                generate(self.source, self.revision, 'minimal', self.base / 'bad', 'kit',
                         review, digest(review.read_bytes()), 'f' * 40)
        with self.assertRaises(SyncError):
            generate(self.source, self.revision, 'minimal', self.base / 'bad', 'kit',
                     review, '0' * 64, 'f' * 40)
        self.assertFalse((self.base / 'bad').exists())

    def test_protocol_confusion_and_tampering(self):
        bundle, pin, _ = self.candidate('admin')
        for channel, approved in (('admin', None), ('kit', pin), ('admin', '0' * 64)):
            with self.assertRaises(SyncError):
                plan(self.root, bundle, channel, approved)
        private = self.base / 'admin-private.json'
        with self.assertRaises(SyncError):
            plan(self.root, private, 'admin', digest(private.read_bytes()))
        original = json.loads(bundle.read_bytes())
        for field, value in (('publication', 'public'), ('owner', 'attacker/repo'),
                             ('generator', 'short'), ('channel', 'kit'), ('format', True)):
            obj = copy.deepcopy(original)
            obj['manifest'][field] = value
            bundle.write_bytes(encoded(obj))
            for approved in (pin, digest(bundle.read_bytes())):
                with self.assertRaises(SyncError):
                    plan(self.root, bundle, 'admin', approved)
        obj = copy.deepcopy(original)
        obj['contents']['AGENTS.md'] += 'tampered'
        bundle.write_bytes(encoded(obj))
        with self.assertRaises(SyncError):
            plan(self.root, bundle, 'admin', digest(bundle.read_bytes()))
        # Format 2 remains private-only, even with a recomputed transport hash.
        obj = json.loads(private.read_bytes())
        obj['manifest']['publication'] = 'public-safe'
        private.write_bytes(encoded(obj))
        with self.assertRaises(SyncError):
            plan(self.root, private, 'admin')

    def test_review_stale_hash_missing_file_and_cli_boundary(self):
        bundle, pin, review = self.candidate()
        original = json.loads(review.read_bytes())
        for mutation in ('hash', 'missing', 'upstream'):
            audit = copy.deepcopy(original)
            if mutation == 'hash':
                audit['files'][PREFIX + SOURCES[0]]['sha256'] = '0' * 64
            elif mutation == 'missing':
                del audit['files'][PREFIX + SOURCES[0]]
            else:
                audit['upstream'] = '0' * 40
            review.write_bytes(encoded(audit))
            with self.assertRaises(SyncError):
                generate(self.source, self.revision, 'minimal', self.base / 'bad', 'kit',
                         review, digest(review.read_bytes()), 'f' * 40)
        args = ['sync', 'plan', '--root', str(self.root), '--bundle', str(bundle)]
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(args), 1)
        self.assertFalse(json.loads(output.getvalue())['ok'])
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(args + ['--public-bundle-sha256', pin]), 0)
        self.assertTrue(json.loads(output.getvalue())['ok'])

    def test_rustcraft_collision_native_preservation_independent_rollback(self):
        protected = {'AGENTS.md': 'RustCraft original rules: just ci; Ubuntu; Windows\n',
                     '.github/DEVELOPMENT_INTERFACE.md': 'existing product interface\n',
                     'AGENTS.local.md': 'just status; just codex-context; just ci\n',
                     '.github/workflows/ci.yml': 'matrix: [ubuntu-latest, windows-latest]\n',
                     'justfile': 'ci: fmt clippy test\n',
                     'docs/ARCHITECTURE.md': 'product architecture\n',
                     'docs/STAGES.md': 'stage register\n'}
        for name, text in protected.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        kit, kit_pin, _ = self.candidate()
        admin, admin_pin, _ = self.candidate('admin')
        self.apply(kit, kit_pin)
        for name, text in protected.items():
            self.assertEqual((self.root / name).read_text(), text)
        with self.assertRaisesRegex(SyncError, 'unmanaged file collision'):
            plan(self.root, admin, 'admin', admin_pin)
        # Stop here: no implicit transformation/overwrite of existing root rules.
        # Adoption/update/rollback independently use another empty disposable root.
        self.root = self.base / 'empty'
        self.root.mkdir()
        self.apply(kit, kit_pin)
        self.apply(admin, admin_pin, 'admin')
        admin_lock = (self.root / ADMIN_LOCK).read_bytes()
        (self.source / SOURCES[0]).write_text('synthetic revision two\n')
        self.revision = self.commit()
        kit2, pin2, _ = self.candidate(suffix='v2')
        self.apply(kit2, pin2)
        self.assertEqual((self.root / ADMIN_LOCK).read_bytes(), admin_lock)
        self.apply(kit, kit_pin)
        kit_lock = (self.root / LOCK).read_bytes()
        (self.source / 'AGENTS.md').write_text('synthetic admin revision two\n')
        self.revision = self.commit()
        admin2, pin2, _ = self.candidate('admin', 'v2')
        self.apply(admin2, pin2, 'admin')
        self.apply(admin, admin_pin, 'admin')
        self.assertEqual((self.root / LOCK).read_bytes(), kit_lock)
        self.assertEqual(plan(self.root, admin, 'admin', admin_pin)[0]['changes'], [])

    def test_public_paths_symlinks_stale_plan_permissions_no_network(self):
        bundle, pin, _ = self.candidate()
        p, _ = plan(self.root, bundle, 'kit', pin)
        with self.assertRaises(SyncError):
            write(self.root, bundle, [], p['plan_sha256'], 'kit', pin)
        obj = json.loads(bundle.read_bytes())
        for name in ('../escape', '.engineering-kit/lock.json', '.engineering-kit/a/b'):
            bad = copy.deepcopy(obj)
            bad['manifest']['source']['files'][name] = digest(b'x')
            bad['contents'][name] = 'x'
            bundle.write_bytes(encoded(bad))
            with self.assertRaises(SyncError):
                plan(self.root, bundle, 'kit', digest(bundle.read_bytes()))
        bundle.write_bytes(encoded(obj))
        alias = self.root / '.engineering-kit'
        alias.symlink_to(self.source, target_is_directory=True)
        with self.assertRaises(SyncError):
            plan(self.root, bundle, 'kit', pin)
        alias.unlink()
        self.root.rename(self.base / 'moved')
        self.root.mkdir()
        with self.assertRaises(SyncError):
            write(self.root, bundle, [c['path'] for c in p['changes']],
                  p['plan_sha256'], 'kit', pin)
        with mock.patch('subprocess.Popen', side_effect=AssertionError('process')), \
                mock.patch('socket.socket', side_effect=AssertionError('network')):
            self.apply(bundle, pin)
        # Public lock cannot silently enter the private protocol.
        with self.assertRaises(SyncError):
            plan(self.root, self.base / 'kit-private.json')
