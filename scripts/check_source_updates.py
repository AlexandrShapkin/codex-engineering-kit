"""Disposable source-update/rollback proof; trusted local checkouts, no network."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engineering_kit.git_observe import _git
from engineering_kit.source_update import plan_source, record_path, write_source


def snapshot(root):
    result = {}
    for path in root.rglob('*'):
        if path.is_symlink():
            raise ValueError('fixture symlink refused')
        if path.is_file():
            result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def cycle(consumer, sources, revisions):
    head = _git(shutil.which('git'), consumer, ['rev-parse', 'HEAD']).decode().strip()
    with tempfile.TemporaryDirectory(prefix='ek-cycle-') as tmp:
        root = Path(tmp) / 'consumer'
        shutil.copytree(consumer, root, symlinks=True, ignore=shutil.ignore_patterns('.git'))
        before = snapshot(root)
        original = {}
        for channel in ('kit', 'admin'):
            record = record_path(channel)
            original[channel] = json.loads((root / record).read_bytes())
            pin = revisions[channel]
            plan, _ = plan_source(root, sources[channel], pin, channel)
            if plan != plan_source(root, sources[channel], pin, channel)[0]:
                raise ValueError('non-deterministic plan')
            write_source(root, sources[channel], pin, channel,
                         [c['path'] for c in plan['changes']], plan['plan_sha256'])
            if plan_source(root, sources[channel], pin, channel)[0]['changes']:
                raise ValueError('non-idempotent update')
        for channel in ('admin', 'kit'):
            pin = original[channel]['revision']
            plan, _ = plan_source(root, sources[channel], pin, channel)
            write_source(root, sources[channel], pin, channel,
                         [c['path'] for c in plan['changes']], plan['plan_sha256'])
            if json.loads((root / record_path(channel)).read_bytes()) != original[channel]:
                raise ValueError('rollback record semantics differ')
        after = snapshot(root)
        excluded = {record_path(c) for c in ('kit', 'admin')}
        if ({k: v for k, v in before.items() if k not in excluded}
                != {k: v for k, v in after.items() if k not in excluded}):
            raise ValueError('rollback changed unrelated files')
        return {'consumer_head': head, 'upstreams': revisions, 'status': 'PASS',
                'files_preserved': len(before) - 2, 'both_record_semantics_restored': True,
                'record_serialization': 'canonical sorted JSON; use reviewed Git revert for historical formatting',
                'native_ci_executed_in_fixture': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kit', type=Path, required=True)
    parser.add_argument('--kit-revision', required=True)
    parser.add_argument('--template', type=Path, required=True)
    parser.add_argument('--template-revision', required=True)
    parser.add_argument('--consumer', type=Path, action='append', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.kit.resolve() == args.template.resolve():
        parser.error('independent canonical checkouts required')
    if len({p.name for p in args.consumer}) != len(args.consumer):
        parser.error('duplicate consumer names')
    sources = {'kit': args.kit, 'admin': args.template}
    revisions = {'kit': args.kit_revision, 'admin': args.template_revision}
    report = {p.name: cycle(p, sources, revisions) for p in args.consumer}
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
