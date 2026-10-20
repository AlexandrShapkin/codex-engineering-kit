"""Offline, read-only checks of observed release evidence; never tag or publish."""
import argparse
import json
from pathlib import Path
import re
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engineering_kit.git_observe import ObservationError, _git
from engineering_kit.sync import SyncError, load, location, read, sha


def check(source, version, target, ci, project='kit', phase='prepare',
          expected_tag_object=None, release=None, publication='private'):
    if not re.fullmatch(r'v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', version):
        raise SyncError('canonical vMAJOR.MINOR.PATCH required')
    if not sha(target, 40) or project not in ('kit', 'template') or phase not in ('prepare', 'verify'):
        raise SyncError('full target SHA, known project and phase required')
    if publication != 'private':
        raise SyncError('public qualification is blocked pending separate owner and licensing review')
    executable = shutil.which('git')
    if executable is None:
        raise SyncError('git unavailable; no installation attempted')
    def git(*args):
        return _git(executable, Path(source), list(args)).decode().strip()
    if git('rev-parse', target + '^{commit}') != target:
        raise SyncError('target commit unavailable')
    workflow = 'Engineering Kit offline checks' if project == 'kit' else 'Template administration checks'
    job = 'source' if project == 'kit' else 'Administrative integrity (not product CI)'
    required = {job + ' (' + version + ')' for version in ('3.11', '3.12', '3.13')}
    if (not isinstance(ci, dict) or ci.get('headSha') != target
            or ci.get('status') != 'completed' or ci.get('conclusion') != 'success'
            or ci.get('workflowName') != workflow or not isinstance(ci.get('jobs'), list)
            or not required.issubset({j.get('name') for j in ci['jobs'] if isinstance(j, dict)
                                    and isinstance(j.get('name'), str)
                                    and j.get('status') == 'completed' and j.get('conclusion') == 'success'})):
        raise SyncError('successful exact-head native Python matrix evidence required')
    refs = dict(line.split(' ', 1) for line in git('for-each-ref', '--format=%(refname) %(objectname)',
                                                'refs/tags/' + version).splitlines())
    tag_object = refs.get('refs/tags/' + version)
    if phase == 'prepare':
        if tag_object is not None or release is not None or expected_tag_object is not None:
            raise SyncError('version already used or inappropriate prepare evidence')
    else:
        if not sha(expected_tag_object, 40) or tag_object != expected_tag_object:
            raise SyncError('missing or moved tag object')
        if git('cat-file', '-t', tag_object) != 'tag':
            raise SyncError('annotated tag required')
        header = git('cat-file', 'tag', tag_object).split('\n\n', 1)[0].splitlines()
        if ('object ' + target not in header or 'type commit' not in header
                or 'tag ' + version not in header or git('rev-parse', 'refs/tags/' + version + '^{commit}') != target):
            raise SyncError('tag name or target mismatch')
        if (not isinstance(release, dict) or release.get('tag_name') != version
                or release.get('draft') is not False or release.get('prerelease') is not False):
            raise SyncError('published stable release metadata required; 0.x API is still provisional')
    return {'project': project, 'version': version, 'target': target, 'phase': phase,
            'tag_object': tag_object, 'evidence_consistent': True,
            'publication': publication, 'publication_authorized': False,
            'limits': 'Offline observations only; independently verify GitHub evidence, main ancestry, rights and owner authority'}


def json_file(path):
    return load(read(location(path.parent, path.name)) or b'')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--project', choices=('kit', 'template'), required=True)
    parser.add_argument('--version', required=True)
    parser.add_argument('--target', required=True)
    parser.add_argument('--ci-json', type=Path, required=True)
    parser.add_argument('--phase', choices=('prepare', 'verify'), default='prepare')
    parser.add_argument('--expected-tag-object')
    parser.add_argument('--release-json', type=Path)
    parser.add_argument('--publication', default='private')
    args = parser.parse_args()
    try:
        result = check(args.source, args.version, args.target, json_file(args.ci_json),
                       args.project, args.phase, args.expected_tag_object,
                       json_file(args.release_json) if args.release_json else None, args.publication)
    except (SyncError, ObservationError, OSError, UnicodeError) as exc:
        print(json.dumps({'ok': False, 'error': str(exc)}))
        return 1
    print(json.dumps({'ok': True, 'data': result}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
