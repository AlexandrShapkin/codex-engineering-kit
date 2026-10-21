"""Offline, explicitly authorized synchronization of an isolated Kit namespace."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tempfile

from engineering_kit.git_observe import _git


class SyncError(ValueError):
    pass


PREFIX = '.engineering-kit/'
LOCK = PREFIX + 'lock.json'
ADMIN_LOCK = '.project-template/lock.json'
ADMIN_PATHS = frozenset(('AGENTS.md', '.github/DEVELOPMENT_INTERFACE.md',
    '.github/ISSUE_TEMPLATE/task.yml', '.github/pull_request_template.md',
    'docs/WORKFLOW.md', '.project-template/OWNERSHIP.md'))


def channel_lock(channel):
    if channel not in ('kit', 'admin'):
        raise SyncError('unknown synchronization channel')
    return ADMIN_LOCK if channel == 'admin' else LOCK

PROFILES = ('minimal', 'backend', 'infrastructure', 'research')
SOURCES = ('contract/AGENT_COMMON.md', 'contract/DEVELOPMENT_INTERFACE.md',
           'skills/ek-context/SKILL.md', 'skills/ek-verify/SKILL.md',
           'skills/ek-pr-closeout/SKILL.md')


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=True, indent=2) + '\n').encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sha(value, length=64):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{%d}' % length, value)


def managed(path, channel='kit'):
    channel_lock(channel)
    if channel == 'admin':
        if not isinstance(path, str) or path not in ADMIN_PATHS:
            raise SyncError('invalid administrative managed path')
        return path
    if (not isinstance(path, str) or not path.startswith(PREFIX)
            or '\\' in path or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_/.' for c in path)
            or any(p in ('', '.', '..') for p in path.split('/'))
            or str(PurePosixPath(path)) != path or path == LOCK
            or path.startswith(LOCK + "/")):
        raise SyncError('invalid managed path')
    return path


def location(root, name):
    """Reject symlinks in the root and every existing path component."""
    root = Path(os.path.abspath(root))
    target = root / name
    for part in (target, *target.parents):
        if part.is_symlink():
            raise SyncError('symlink path refused')
    for parent in target.parents:
        if parent.exists() and not parent.is_dir():
            raise SyncError('non-directory parent')
    return target


def read(path):
    if os.name != 'posix':
        raise SyncError('safe file reads require POSIX; unsupported platform')
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        return None
    with os.fdopen(fd, 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise SyncError('expected regular file')
        data = stream.read(1024 * 1024 + 1)
    if len(data) > 1024 * 1024:
        raise SyncError('file exceeds 1 MiB limit')
    return data


def load(data):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise SyncError('duplicate JSON key')
            result[key] = value
        return result
    try:
        return json.loads(data, object_pairs_hook=unique)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise SyncError('invalid JSON') from exc


def metadata(obj, channel='kit', public=False):
    channel_lock(channel)
    if public:
        fields = {'format', 'publication', 'channel', 'owner', 'generator', 'review', 'source'}
        if (not isinstance(obj, dict) or set(obj) != fields
                or type(obj['format']) is not int or obj['format'] != 3
                or obj['publication'] != 'public-safe' or obj['channel'] != channel
                or obj['owner'] != ('AlexandrShapkin/project-template' if channel == 'admin'
                                    else 'AlexandrShapkin/codex-engineering-kit')
                or not sha(obj['generator'], 40) or not sha(obj['review'])):
            raise SyncError('invalid public distribution provenance')
        source = metadata(obj['source'], channel)
        expected = (ADMIN_PATHS if channel == 'admin' else
                    {PREFIX + n for n in SOURCES} | {PREFIX + 'PROFILE.md'})
        if set(source['files']) != set(expected):
            raise SyncError('public distribution requires exact managed file set')
        return obj
    fields = {'format', 'upstream', 'profile', 'files'}
    if channel == 'admin':
        fields |= {'publication', 'owner'}
    if (not isinstance(obj, dict) or set(obj) != fields
            or type(obj['format']) is not int
            or obj['format'] != (2 if channel == 'admin' else 1)
            or not sha(obj['upstream'], 40)
            or obj['profile'] not in (('administrative',) if channel == 'admin' else PROFILES)
            or not isinstance(obj['files'], dict) or not obj['files']):
        raise SyncError('invalid manifest')
    if channel == 'admin' and (obj['publication'] != 'private'
            or obj['owner'] != 'AlexandrShapkin/project-template'):
        raise SyncError('invalid administrative provenance/classification')
    for name, value in obj['files'].items():
        managed(name, channel)
        if not sha(value):
            raise SyncError('invalid file hash')
    for name in obj['files']:
        if any(str(p) in obj['files'] for p in PurePosixPath(name).parents):
            raise SyncError('overlapping file paths')
    return obj


def bundle_read(path, channel='kit', public_bundle_sha256=None):
    raw = read(location(Path(path).parent, Path(path).name)) or b''
    public = public_bundle_sha256 is not None
    if public and (not sha(public_bundle_sha256) or digest(raw) != public_bundle_sha256):
        raise SyncError('approved public bundle SHA-256 mismatch')
    obj = load(raw)
    if not isinstance(obj, dict) or set(obj) != {'manifest', 'contents'}:
        raise SyncError('invalid bundle')
    manifest = metadata(obj['manifest'], channel, public)
    source = manifest['source'] if public else manifest
    contents = obj['contents']
    if not isinstance(contents, dict) or set(contents) != set(source['files']):
        raise SyncError('bundle file set mismatch')
    data = {}
    for name, value in contents.items():
        if not isinstance(value, str):
            raise SyncError('invalid file content')
        data[name] = value.encode('utf-8')
        if digest(data[name]) != source['files'][name]:
            raise SyncError('bundle hash mismatch')
    return manifest, data


def export(source, revision, profile, output, channel='kit'):
    channel_lock(channel)
    if not sha(revision, 40) or profile not in (('administrative',) if channel == 'admin' else PROFILES):
        raise SyncError('full commit SHA and known profile required')
    executable = shutil.which('git')
    if executable is None:
        raise SyncError('git unavailable; no installation attempted')
    def git(*args):
        return _git(executable, Path(source), list(args))
    if git('rev-parse', revision + '^{commit}').decode().strip() != revision:
        raise SyncError('source is not a commit')
    contents = {}
    sources = {PREFIX + name: name for name in SOURCES}
    sources[PREFIX + 'PROFILE.md'] = 'profiles/sync/' + profile + '.md'
    if channel == 'admin':
        sources = {name: name for name in sorted(ADMIN_PATHS)}
    for destination, name in sources.items():
        # Git tree mode is part of provenance: never export a symlink/blob alias.
        entry = git('ls-tree', revision, '--', name).decode()
        if not entry.startswith('100644 blob '):
            raise SyncError('source must be a regular tracked file')
        contents[destination] = git('show', revision + ':' + name).decode('utf-8')
    manifest = {'format': 1, 'upstream': revision, 'profile': profile,
                'files': {n: digest(v.encode()) for n, v in contents.items()}}
    if channel == 'admin':
        manifest.update(format=2, publication='private', owner='AlexandrShapkin/project-template')
    metadata(manifest, channel)
    path = location(Path(output).parent, Path(output).name)
    with path.open('xb') as stream:
        stream.write(encoded({'manifest': manifest, 'contents': contents}))
    return manifest


def plan(root, bundle, channel='kit', public_bundle_sha256=None):
    lock = channel_lock(channel)
    root = Path(os.path.abspath(root))
    if not root.is_dir():
        raise SyncError('target root must exist')
    manifest, contents = bundle_read(bundle, channel, public_bundle_sha256)
    public = public_bundle_sha256 is not None
    source = manifest['source'] if public else manifest
    lock_data = read(location(root, lock))
    old = metadata(load(lock_data), channel, public) if lock_data is not None else None
    previous = (old['source'] if public else old)['files'] if old else {}
    return file_plan(root, lock, lock_data, previous, manifest, contents,
                     source['upstream'], source['profile'])


def file_plan(root, lock, lock_data, previous, manifest, contents, upstream, profile):
    """Shared drift checks, state-bound token and deterministic path plan."""
    root = Path(os.path.abspath(root))
    changes = []
    snapshots = {lock: lock_data}
    for name in sorted(set(previous) | set(contents)):
        current = read(location(root, name))
        snapshots[name] = current
        if name in previous:
            if current is None or digest(current) != previous[name]:
                raise SyncError('managed file locally modified or missing: ' + name)
        elif current is not None:
            raise SyncError('unmanaged file collision: ' + name)
        desired = contents.get(name)
        if desired != current:
            changes.append({'path': name, 'action': 'delete' if desired is None else
                            ('create' if current is None else 'update')})
    contents[lock] = encoded(manifest)
    if contents[lock] != lock_data:
        changes.append({'path': lock, 'action': 'create' if lock_data is None else 'update'})
    identity = root.stat()
    token = digest(encoded({'consumer': {'path': str(root), 'device': identity.st_dev,
                                         'inode': identity.st_ino},
                            'manifest': manifest, 'changes': changes,
                            'before': {n: digest(v) if v is not None else None
                                       for n, v in snapshots.items()}}))
    return {'changes': changes, 'plan_sha256': token, 'upstream': upstream,
            'profile': profile}, contents


def write(root, bundle, allowed, token, channel='kit', public_bundle_sha256=None):
    result, contents = plan(root, bundle, channel, public_bundle_sha256)
    return apply_plan(root, result, contents, allowed, token)


def apply_plan(root, result, contents, allowed, token):
    """Shared exact permission preflight and per-file replacement; record last."""
    paths = {c['path'] for c in result['changes']}
    if token != result['plan_sha256'] or set(allowed) != paths:
        raise SyncError('exact plan SHA and exact --allow path set required')
    # Complete preflight before any mutation. Caller must exclude concurrent writers.
    for change in result['changes']:
        path = location(root, change['path'])
        for parent in path.parents:
            if parent.exists() and not parent.is_dir():
                raise SyncError('non-directory parent')
    for change in result['changes']:
        path = location(root, change['path'])
        if change['action'] == 'delete':
            path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            # Exclusive sibling temp; atomic per-file replacement, lock written last.
            fd, temp = tempfile.mkstemp(prefix='.ek-', dir=path.parent)
            try:
                with os.fdopen(fd, 'wb') as stream:
                    stream.write(contents[change['path']])
                os.replace(temp, path)
            finally:
                if os.path.exists(temp):
                    os.unlink(temp)
    return result
