"""Real, independent Git sources guard the opt-in fixture's source routing."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

from engineering_kit.git_observe import ObservationError
from engineering_kit.sync import ADMIN_PATHS, SOURCES, SyncError, bundle_read
from scripts import check_public_fixture as fixture


class PublicFixtureSourceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.kit, kit_revision = self.repository('kit', (*SOURCES, 'profiles/sync/minimal.md'))
        self.template, template_revision = self.repository('template', ADMIN_PATHS)
        for name, value in (('KIT_REVISION', kit_revision), ('TEMPLATE_REVISION', template_revision)):
            patch = mock.patch.object(fixture, name, value)
            patch.start()
            self.addCleanup(patch.stop)
        self.output = self.base / 'exports'
        self.output.mkdir()

    def repository(self, name, paths):
        root = self.base / name
        root.mkdir()
        def git(*args):
            return subprocess.check_output(['git', '-C', str(root), *args]).decode().strip()
        git('init', '-q')
        for name in sorted(paths):
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(str(root.name) + ': synthetic ' + name + '\n')
        git('add', '.')
        git('-c', 'user.name=Offline Fixture', '-c', 'user.email=test@example.invalid',
            'commit', '-qm', 'independent source fixture')
        return root, git('rev-parse', 'HEAD')

    def test_separate_sources_export_repeatably_without_network(self):
        with mock.patch('socket.socket', side_effect=AssertionError('network')):
            bundles, evidence = fixture.private_baselines(self.kit, self.template, self.output)
        for channel, revision in (('kit', fixture.KIT_REVISION), ('admin', fixture.TEMPLATE_REVISION)):
            manifest, _ = bundle_read(bundles[channel], channel)
            self.assertEqual(manifest['upstream'], revision)
            self.assertTrue(evidence[channel]['repeatable'])
        self.assertNotEqual(fixture.KIT_REVISION, fixture.TEMPLATE_REVISION)

    def test_wrong_git_source_fails_before_exports(self):
        # Both roots are real repos; neither contains the other upstream's objects.
        with self.assertRaises(ObservationError):
            fixture.private_baselines(self.template, self.kit, self.output)
        self.assertEqual(list(self.output.iterdir()), [])

    def test_same_checkout_or_alias_cannot_supply_both_channels(self):
        alias = self.base / 'kit-alias'
        alias.symlink_to(self.kit, target_is_directory=True)
        for template in (self.kit, alias):
            with self.assertRaisesRegex(SyncError, 'distinct Git checkouts'):
                fixture.private_baselines(self.kit, template, self.output)
        self.assertEqual(list(self.output.iterdir()), [])

    def test_missing_template_commit_fails_before_kit_export(self):
        with mock.patch.object(fixture, 'TEMPLATE_REVISION', '0' * 40):
            with self.assertRaises(ObservationError):
                fixture.private_baselines(self.kit, self.template, self.output)
        self.assertEqual(list(self.output.iterdir()), [])
