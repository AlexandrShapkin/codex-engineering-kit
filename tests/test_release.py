"""Release observations use synthetic tags in disposable repositories only."""
import copy
from pathlib import Path
import subprocess
import tempfile
import unittest

from engineering_kit.sync import SyncError
from scripts.check_release import check


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.git('init', '-q')
        self.git('config', 'user.name', 'Synthetic Release Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        (self.root / 'data').write_text('synthetic')
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')
        self.target = self.git('rev-parse', 'HEAD')
        self.ci = {'headSha': self.target, 'status': 'completed', 'conclusion': 'success',
                   'workflowName': 'Engineering Kit offline checks',
                   'jobs': [{'name': 'source (' + v + ')', 'status': 'completed', 'conclusion': 'success'}
                            for v in ('3.11', '3.12', '3.13')]}
        self.release = {'tag_name': 'v0.1.0', 'draft': False, 'prerelease': False}

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.root), *args], stderr=subprocess.DEVNULL).decode().strip()

    def verify(self, oid=None, release=None, target=None):
        return check(self.root, 'v0.1.0', target or self.target, self.ci, phase='verify',
                     expected_tag_object=oid or self.git('rev-parse', 'v0.1.0'),
                     release=self.release if release is None else release)

    def test_prepare_and_verify_never_authorize_publication(self):
        self.assertFalse(check(self.root, 'v0.1.0', self.target, self.ci)['publication_authorized'])
        self.git('tag', '-a', 'v0.1.0', '-m', 'synthetic fixture')
        self.assertFalse(self.verify()['publication_authorized'])
        with self.assertRaises(SyncError):
            check(self.root, 'v0.1.0', self.target, self.ci)

    def test_noncanonical_version_and_public_classification_rejected(self):
        for version in ('0.1.0', 'v00.1.0', 'v0.01.0', 'v0.1.0-extra', 'v0.1.0\n'):
            with self.assertRaises(SyncError):
                check(self.root, version, self.target, self.ci)
        for classification in ('public', 'public-safe', ''):
            with self.assertRaises(SyncError):
                check(self.root, 'v0.1.0', self.target, self.ci, publication=classification)

    def test_wrong_failed_incomplete_or_untrusted_ci_rejected(self):
        for key, value in (('headSha', 'a' * 40), ('status', 'in_progress'),
                           ('conclusion', 'failure'), ('workflowName', 'smoke'), ('jobs', [])):
            ci = copy.deepcopy(self.ci)
            ci[key] = value
            with self.assertRaises(SyncError):
                check(self.root, 'v0.1.0', self.target, ci)
        ci = copy.deepcopy(self.ci)
        ci['jobs'][0]['conclusion'] = 'skipped'
        with self.assertRaises(SyncError):
            check(self.root, 'v0.1.0', self.target, ci)

    def test_reused_release_lightweight_and_moved_tag_rejected(self):
        with self.assertRaises(SyncError):
            check(self.root, 'v0.1.0', self.target, self.ci, release=self.release)
        self.git('tag', 'v0.1.0')
        with self.assertRaises(SyncError):
            self.verify()
        self.git('tag', '-fa', 'v0.1.0', '-m', 'synthetic annotation')
        recorded = self.git('rev-parse', 'v0.1.0')
        self.git('tag', '-fa', 'v0.1.0', '-m', 'synthetic moved annotation same commit')
        with self.assertRaises(SyncError):
            self.verify(oid=recorded)

    def test_mismatched_tag_target_and_release_rejected(self):
        (self.root / 'data').write_text('second synthetic commit')
        self.git('commit', '-qam', 'second fixture')
        self.git('tag', '-a', 'v0.1.0', '-m', 'wrong target')
        with self.assertRaises(SyncError):
            self.verify()
        self.git('tag', '-fa', 'v0.1.0', self.target, '-m', 'synthetic fixture')
        for key, value in (('tag_name', 'v0.2.0'), ('draft', True), ('prerelease', True)):
            release = copy.deepcopy(self.release)
            release[key] = value
            with self.assertRaises(SyncError):
                self.verify(release=release)

    def test_template_uses_independent_native_matrix(self):
        with self.assertRaises(SyncError):
            check(self.root, 'v0.1.0', self.target, self.ci, project='template')
        ci = copy.deepcopy(self.ci)
        ci['workflowName'] = 'Template administration checks'
        for job in ci['jobs']:
            job['name'] = job['name'].replace('source', 'Administrative integrity (not product CI)')
        self.assertTrue(check(self.root, 'v0.1.0', self.target, ci, project='template')['evidence_consistent'])

    def test_annotation_name_and_missing_external_pin_rejected(self):
        self.git('tag', '-a', 'v0.2.0', '-m', 'different name')
        self.git('update-ref', 'refs/tags/v0.1.0', self.git('rev-parse', 'v0.2.0'))
        with self.assertRaises(SyncError):
            self.verify()
        with self.assertRaises(SyncError):
            check(self.root, 'v0.1.0', self.target, self.ci, phase='verify', release=self.release)
