"""Portable source-contract and negative-case tests."""
import tempfile
import unittest
from pathlib import Path
from engineering_kit.contract import ContractError, ROOT, canonical, requirements, read, check, self_check


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
            block + "\n<!-- agent-project: " + name + " -->\n" + "\n".join(markers) + "\n")

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


if __name__ == "__main__":
    unittest.main()
