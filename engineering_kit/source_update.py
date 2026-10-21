"""Offline updates of reviewed source migrations; never a distribution artifact."""
from pathlib import Path
import os
import shutil

from engineering_kit.git_observe import _git
from engineering_kit.sync import (ADMIN_PATHS, PREFIX, SOURCES, SyncError,
                                 apply_plan, channel_lock, digest, file_plan,
                                 load, location, read, sha)


def source_map(channel):
    channel_lock(channel)
    if channel == 'admin':
        return {name: name for name in ADMIN_PATHS}
    return {**{PREFIX + name: name for name in SOURCES},
            PREFIX + 'PROFILE.md': 'profiles/sync/minimal.md'}


def record_path(channel):
    channel_lock(channel)
    return ('.project-template/' if channel == 'admin' else PREFIX) + 'source.json'


def owner(channel):
    channel_lock(channel)
    return 'AlexandrShapkin/' + ('project-template' if channel == 'admin'
                               else 'codex-engineering-kit')


def validate_record(obj, channel):
    paths = source_map(channel)
    if (not isinstance(obj, dict)
            or set(obj) != {'method', 'repository', 'revision', 'license_at', 'files'}
            or obj['method'] != 'reviewed-public-source-migration'
            or obj['repository'] != owner(channel)
            or not sha(obj['revision'], 40) or not sha(obj['license_at'], 40)
            or not isinstance(obj['files'], dict) or set(obj['files']) != set(paths)):
        raise SyncError('invalid reviewed source record')
    for name, entry in obj['files'].items():
        if (not isinstance(entry, dict) or set(entry) != {'source_path', 'sha256'}
                or entry['source_path'] != paths[name] or not sha(entry['sha256'])):
            raise SyncError('invalid reviewed source mapping/hash')
    return obj


def plan_source(root, source, revision, channel):
    """Compare a trusted canonical checkout to an existing reviewed installation.

    No adoption, lock conversion, fetching, publication or source-owner assertion.
    Caller independently authenticates source, rights and target SHA acceptance.
    """
    channel_lock(channel)
    root = Path(os.path.abspath(root))
    source = Path(os.path.abspath(source))
    location(root, record_path(channel))
    location(source, 'LICENSE')
    if not root.is_dir() or not source.is_dir() or root == source:
        raise SyncError('distinct existing source and consumer roots required')
    if not sha(revision, 40):
        raise SyncError('full source commit SHA required')
    executable = shutil.which('git')
    if executable is None:
        raise SyncError('git unavailable; no installation attempted')

    def git(*args):
        return _git(executable, source, list(args))

    # Require the actual source Git root, not an accidental nested checkout path.
    if Path(git('rev-parse', '--show-toplevel').decode().strip()) != source:
        raise SyncError('source must be its Git root')

    def commit(pin):
        if git('rev-parse', pin + '^{commit}').decode().strip() != pin:
            raise SyncError('source is not a commit')

    def blob(pin, name):
        if not git('ls-tree', pin, '--', name).startswith(b'100644 blob '):
            raise SyncError('source must be a regular tracked file')
        data = git('show', pin + ':' + name)
        data.decode('utf-8')
        return data

    # A lock is a different accepted protocol, never overwritten or bypassed.
    if read(location(root, channel_lock(channel))) is not None:
        raise SyncError('source records and bundle locks cannot be mixed')
    record = record_path(channel)
    raw = read(location(root, record))
    if raw is None:
        raise SyncError('reviewed source installation required; no initial adoption')
    old = validate_record(load(raw), channel)
    for pin in {revision, old['revision'], old['license_at']}:
        commit(pin)
    # Preserve the independently reviewed notice identity; changes need review.
    license_data = blob(old['license_at'], 'LICENSE')
    license_entry = git('ls-tree', revision, '--', 'LICENSE')
    if license_entry and license_data != blob(revision, 'LICENSE'):
        raise SyncError('license changed; separate rights review required')
    contents = {}
    for name, path in sorted(source_map(channel).items()):
        if digest(blob(old['revision'], path)) != old['files'][name]['sha256']:
            raise SyncError('installed provenance differs from pinned source')
        contents[name] = blob(revision, path)
        # Accepted migrations predate LICENSE. Permit those exact source bytes
        # only when also present at the separately retained licensing identity.
        # This is a consistency check, never an inferred owner rights approval.
        if not license_entry and contents[name] != blob(old['license_at'], path):
            raise SyncError('unlicensed source differs from reviewed licensing snapshot')
    new = {**old, 'revision': revision,
           'files': {name: {'source_path': source_map(channel)[name],
                            'sha256': digest(data)} for name, data in contents.items()}}
    result, contents = file_plan(root, record, raw,
                               {n: v['sha256'] for n, v in old['files'].items()},
                               new, contents, revision,
                               'administrative' if channel == 'admin' else 'minimal')
    result['diffs'] = {c['path']: {'before_sha256': digest(read(location(root, c['path']))),
                                  'after_sha256': digest(contents[c['path']])}
                       for c in result['changes']}
    return result, contents


def write_source(root, source, revision, channel, allowed, token):
    result, contents = plan_source(root, source, revision, channel)
    return apply_plan(root, result, contents, allowed, token)
