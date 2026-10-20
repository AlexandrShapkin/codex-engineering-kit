"""Portable source-contract and negative-case tests."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock
import engineering_kit.contract as contract
from engineering_kit.contract import ContractError, ROOT, canonical, requirements, read, check, self_check


# Independent examples of original prohibitions from the four fixed Draft HEADs.
# Test consumers must not derive their safety sentences from mutable profiles.
TEST_CRITICAL = {
    "codex-smart": "PR #125 is prohibited from merge; PR #164 remains\n"
                   "experimental and must not be activated.",
    "relayforge": "Do not change runtime, grants, services,\nlauncher or binaries.\n"
                  "All permitted local Cargo checks require explicit isolated\n"
                  "`CARGO_TARGET_DIR`.",
    "assistant-hub": "The current task authorizes Draft PRs only; historical standing merge language\n"
                     "below does not authorize merging these changes or any runtime operation.",
    "rustcraft": "Full native gate: `just ci`,\n"
                 "plus mandatory GitHub CI on Ubuntu and Windows. Smoke alone is insufficient.",
}


class ContractTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name)
        (self.path / ".github").mkdir()
        _, i = canonical()
        (self.path / ".github/DEVELOPMENT_INTERFACE.md").write_text(i)

    def consumer(self, name="rustcraft", requirements_override=None):
        markers = requirements()[name] if requirements_override is None else requirements_override
        block = read(ROOT, "contract/AGENT_COMMON.md")
        (self.path / "AGENTS.md").write_text(
            block + "\n<!-- agent-project: " + name + " -->\n" + "\n".join(markers)
            + "\n" + TEST_CRITICAL.get(name, "") + "\n")

    def test_self(self):
        self_check()

    def test_all_profiles(self):
        for name in requirements():
            with self.subTest(name=name):
                self.consumer(name)
                check(self.path, name)

    def test_missing_native_gate(self):
        self.consumer(requirements_override=("just ci",))
        with self.assertRaisesRegex(ContractError, "mandatory"):
            check(self.path, "rustcraft")

    def test_wrong_identity(self):
        self.consumer("relayforge")
        with self.assertRaisesRegex(ContractError, "identity"):
            check(self.path, "rustcraft")

    def test_joint_shared_drift(self):
        self.consumer()
        for f in (self.path / "AGENTS.md", self.path / ".github/DEVELOPMENT_INTERFACE.md"):
            f.write_text(f.read_text().replace("Never use RDC", "Sometimes use RDC"))
        with self.assertRaisesRegex(ContractError, "drift"):
            check(self.path, "rustcraft")

    def test_duplicate_markers(self):
        self.consumer()
        p = self.path / "AGENTS.md"
        p.write_text(p.read_text() + "<!-- shared-agent:start -->\n")
        with self.assertRaisesRegex(ContractError, "markers"):
            check(self.path, "rustcraft")

    def test_symlink_refusal(self):
        self.consumer()
        p = self.path / "AGENTS.md"
        alternate = self.path / "other.txt"
        alternate.write_bytes(p.read_bytes())
        p.unlink()
        p.symlink_to(alternate)
        with self.assertRaisesRegex(ContractError, "symlink"):
            check(self.path, "rustcraft")

    def test_oversized_refusal(self):
        self.consumer()
        (self.path / "AGENTS.md").write_bytes(b"x" * (256 * 1024 + 1))
        with self.assertRaisesRegex(ContractError, "oversized"):
            check(self.path, "rustcraft")

    def test_path_traversal(self):
        with self.assertRaises(ContractError):
            read(self.path, "../secret.txt")


    def test_profile_weakening_is_detected_even_when_consumers_change(self):
        original = read
        def changed(root, relative):
            contents = original(root, relative)
            if relative == "profiles/products.json":
                data = json.loads(contents)
                data["required"]["rustcraft"] = ["docs/INDEX.md"]
                return json.dumps(data)
            return contents
        with mock.patch.object(contract, "read", side_effect=changed):
            with self.assertRaisesRegex(ContractError, "baseline"):
                self_check()

    def test_fixed_native_baseline_is_independent_of_positive_fixture(self):
        expected = {"rustcraft": "just ci", "codex-smart": "just security",
                    "relayforge": "CARGO_TARGET_DIR",
                    "assistant-hub": "python scripts/check_public_tree.py --include-untracked"}
        for project, gate in expected.items():
            with self.subTest(project=project):
                self.assertIn(gate, requirements()[project])

    def test_inverted_merge_veto_is_rejected(self):
        self.consumer("codex-smart")
        path = self.path / "AGENTS.md"
        path.write_text(path.read_text().replace(
            "PR #125 is prohibited from merge",
            "PR #125 is permitted to merge"))
        with self.assertRaisesRegex(ContractError, "critical product prohibition"):
            check(self.path, "codex-smart")

    def test_inverted_relayforge_runtime_veto_is_rejected(self):
        self.consumer("relayforge")
        path = self.path / "AGENTS.md"
        path.write_text(path.read_text().replace(
            "Do not change runtime, grants, services,",
            "You may change runtime, grants, services,"))
        with self.assertRaisesRegex(ContractError, "critical product prohibition"):
            check(self.path, "relayforge")

    def test_parent_symlink_before_root_is_rejected(self):
        self.consumer()
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            real = parent / "real"
            real.mkdir()
            self.path.rename(real / "consumer")
            (parent / "alias").symlink_to(real, target_is_directory=True)
            with self.assertRaisesRegex(ContractError, "symlink"):
                check(parent / "alias" / "consumer", "rustcraft")

    def test_leaf_swap_to_external_symlink_never_reads_target(self):
        self.consumer()
        path = self.path / "AGENTS.md"
        outside = self.path / "outside.txt"
        outside.write_text("PRIVATE CONTENT")
        native_open = os.open
        swapped = False
        def swap(name, flags, *args, **kwargs):
            nonlocal swapped
            if name == "AGENTS.md" and not swapped:
                swapped = True
                path.rename(self.path / "saved-agent")
                path.symlink_to(outside)
            return native_open(name, flags, *args, **kwargs)
        # The mocked os.open remains descriptor-aware; preserve the platform
        # capability declaration so the test reaches the leaf-opening race.
        with mock.patch("os.open", side_effect=swap) as wrapped_open:
            with mock.patch.object(os, "supports_dir_fd",
                                   os.supports_dir_fd | {wrapped_open}):
                with self.assertRaisesRegex(ContractError, "symlink"):
                    check(self.path, "rustcraft")
        self.assertTrue(swapped)

    def test_reverse_markers_are_controlled_failure(self):
        self.consumer()
        path = self.path / "AGENTS.md"
        text = path.read_text()
        path.write_text("<!-- shared-agent:end -->\n" +
                        text.replace("<!-- shared-agent:end -->", ""))
        with self.assertRaisesRegex(ContractError, "wrong order"):
            check(self.path, "rustcraft")


if __name__ == "__main__":
    unittest.main()
