"""Kit adoption integrity; shared policy content remains Template-owned."""
import json
from pathlib import Path

from engineering_kit.sync import ADMIN_PATHS, ADMIN_LOCK, bundle_read, digest, location, metadata

ADMIN_SOURCE = '89cecbb4f44506f79ad3c5a22cb713429adea8a5'
TEMPLATE_MAIN = '5087295b7e571e87c3f70f721e26ff4ca7a2e315'
# Independently reviewed source/export bytes; updating requires a migration PR.
SOURCE_HASHES = {
    '.project-template/bundles/initial.json':
        'a6050771ad619e5c90d36670429f1cf4dcc7ac705d22b4b25875c22e285a73ed',
    '.github/labels.json':
        'd84d08b1828df0ce1f07d8330ff48090513369b2e1463efaae50c7bde145acd8',
    'scripts/check_github_metadata.py':
        '8fb0a60013519e308d13e66464c4e960c976e5b4bb611f73c45beb280bd8d3dc',
}


def check(root):
    root = Path(root)
    for name, expected in SOURCE_HASHES.items():
        path = location(root, name)
        if path.is_symlink() or digest(path.read_bytes()) != expected:
            raise ValueError('Template provenance drift: ' + name)
    manifest, contents = bundle_read(root / '.project-template/bundles/initial.json', 'admin')
    lock = json.loads(location(root, ADMIN_LOCK).read_text())
    metadata(lock, 'admin')
    if lock != manifest or lock['upstream'] != ADMIN_SOURCE or set(contents) != ADMIN_PATHS:
        raise ValueError('administrative lock/source drift')
    for name, expected in contents.items():
        path = location(root, name)
        if path.is_symlink() or path.read_bytes() != expected:
            raise ValueError('policy discovery/content drift: ' + name)
    for name in ('AGENTS.local.md', 'docs/INDEX.md', 'docs/PROJECT.md', 'docs/UPGRADING.md'):
        path = location(root, name)
        if path.is_symlink() or not path.is_file() or not path.read_text().strip():
            raise ValueError('missing local entrypoint: ' + name)
    local = (root / 'AGENTS.local.md').read_text()
    for gate in ('python3 -B scripts/check_contract.py --self-check',
                 'python3 -B -m unittest discover -s tests -v',
                 'exact-head GitHub CI', 'Do not execute consumer commands',
                 'Never install dependencies, fetch secrets, change global Codex config',
                 'use RDC, run a production build, deploy, merge',
                 'MIT LICENSE applies to owner-controlled source'):
        if gate not in local:
            raise ValueError('missing Kit gate: ' + gate)
