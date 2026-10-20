"""Read-only RustCraft snapshot into an automatically removed synthetic fixture."""
import argparse
import json
from pathlib import Path
import shutil
import sys
script_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(script_root))
sys.path.insert(0, str(script_root / 'tests'))
from test_distribution import DistributionTests
from engineering_kit.git_observe import _git
from engineering_kit.sync import SyncError, digest, encoded, export, plan
KIT_REVISION = 'e647d9d535eb9b55f2a6df55c2bf5e4b9a47957d'
TEMPLATE_REVISION = '0a53f56dba841675b3203a76e33594fee1a73b9f'


def private_baselines(kit_source, template_source, directory):
    """Export from separate canonical checkouts; never fetch/import Git objects."""
    executable = shutil.which('git')
    if executable is None:
        raise SyncError('git unavailable; no installation attempted')
    roots = []
    sources = [('kit', Path(kit_source), KIT_REVISION, 'minimal'),
               ('admin', Path(template_source), TEMPLATE_REVISION, 'administrative')]
    # Validate BOTH sources before generating any evidence or reading RustCraft.
    for channel, root, revision, profile in sources:
        actual = Path(_git(executable, root, ['rev-parse', '--show-toplevel']).decode().strip()).resolve()
        if actual != root.resolve():
            raise SyncError('explicit Git checkout root required: ' + channel)
        roots.append(actual)
    if roots[0] == roots[1]:
        raise SyncError('Kit and Template require distinct Git checkouts')
    for channel, root, revision, profile in sources:
        resolved = _git(executable, root, ['rev-parse', revision + '^{commit}']).decode().strip()
        if resolved != revision:
            raise SyncError('pinned source commit unavailable: ' + channel)
    bundles = {}
    exports = {}
    for channel, root, revision, profile in sources:
        private = directory / (channel + '-actual-private.json')
        export(root, revision, profile, private, channel)
        repeat = directory / (channel + '-actual-repeat.json')
        export(root, revision, profile, repeat, channel)
        assert private.read_bytes() == repeat.read_bytes()
        exports[channel] = {'upstream': revision, 'repeatable': True,
                            'bundle_sha256': digest(private.read_bytes())}
        bundles[channel] = private
    return bundles, exports


def run_fixture(kit_source, template_source, rustcraft_source, output):
    case = DistributionTests()
    case.setUp()
    try:
        bundles, exports = private_baselines(kit_source, template_source, case.base)
        rejected = []
        for channel, private in bundles.items():
            try:
                plan(case.root, private, channel, digest(private.read_bytes()))
            except SyncError:
                rejected.append(channel)
            else:
                raise AssertionError("private accepted")
        source = rustcraft_source
        def git(*args):
            return _git(shutil.which('git'), source, list(args))
        head = git('rev-parse', 'HEAD').decode().strip()
        names = git('ls-tree', '-r', '--name-only', head, '--', 'AGENTS.md',
                    '.github/DEVELOPMENT_INTERFACE.md', '.github/workflows', 'justfile',
                    'docs/ARCHITECTURE.md', 'docs/INDEX.md', 'docs/stages.toml', 'docs/stages').decode().splitlines()
        before = {}
        for name in names:
            data = git('show', head + ':' + name)
            target = case.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            before[name] = digest(data)
        assert '\nci:' in (case.root / 'justfile').read_text()
        ci = (case.root / '.github/workflows/ci.yml').read_text()
        assert 'ubuntu-latest' in ci and 'windows-latest' in ci
        kit, pin, _ = case.candidate()
        first, _ = plan(case.root, kit, 'kit', pin)
        case.apply(kit, pin)
        admin, pin, _ = case.candidate('admin')
        try:
            plan(case.root, admin, 'admin', pin)
        except SyncError as error:
            collision = str(error)
            assert collision == 'unmanaged file collision: AGENTS.md'
        else:
            raise AssertionError('admin overwrote existing rules')
        after = {n: digest((case.root / n).read_bytes()) for n in names}
        assert before == after
        assert git('rev-parse', 'HEAD').decode().strip() == head
        report = {'rustcraft_read_only_head': head, 'scope': 'disposable local copies only',
                  'synthetic_public_bytes': True, 'real_private_channels_rejected': rejected,
                  'private_baseline_reproducibility': exports,
                  'kit_initial_changes': first['changes'], 'existing_interface': '.github/DEVELOPMENT_INTERFACE.md' in names,
                  'admin_agents_collision': collision, 'native_bytes_unchanged': before == after,
                  'copied_file_sha256_before_and_after': before,
                  'native_gates_retained': ['just ci', 'ubuntu-latest', 'windows-latest'],
                  'native_build_and_migration_ci': 'UNVERIFIED; no Rust commands executed'}
        with output.open('xb') as stream:
            stream.write(encoded(report))
        print(json.dumps({'copied_files': len(names), 'unchanged': True, 'private_channels_rejected': rejected,
                          'collisions': [collision]}))
    finally:
        case.doCleanups()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kit-source', type=Path, required=True)
    parser.add_argument('--template-source', type=Path, required=True)
    parser.add_argument('--rustcraft-source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run_fixture(args.kit_source, args.template_source, args.rustcraft_source, args.output)


if __name__ == '__main__':
    main()
