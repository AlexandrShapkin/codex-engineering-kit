"""Offline candidate generation only. No upload, signing or publication authority."""
from pathlib import Path
import tempfile

from engineering_kit.sync import (SyncError, bundle_read, digest, encoded, export,
                                  load, location, metadata, read, sha)


def generate(source, revision, profile, output, channel, review, review_sha256,
             generator_revision):
    """Review is an external, digest-pinned classification of exact source bytes.

    The output remains private staging until the owner authorizes its full digest.
    Neither this function nor its review input can attest that authorization.
    """
    raw = read(location(Path(review).parent, Path(review).name)) or b''
    if not sha(review_sha256) or digest(raw) != review_sha256:
        raise SyncError('review SHA-256 mismatch')
    audit = load(raw)
    if (not isinstance(audit, dict)
            or set(audit) != {'format', 'channel', 'upstream', 'files'}
            or type(audit['format']) is not int or audit['format'] != 1
            or audit['channel'] != channel or audit['upstream'] != revision
            or not isinstance(audit['files'], dict) or not sha(generator_revision, 40)):
        raise SyncError('invalid distribution review')
    with tempfile.TemporaryDirectory(prefix='ek-candidate-') as temporary:
        bundle = Path(temporary) / 'source.json'
        export(source, revision, profile, bundle, channel)
        original, contents = bundle_read(bundle, channel)
    expected = {name: {'sha256': value, 'classification': 'PUBLIC-SAFE'}
                for name, value in original['files'].items()}
    if audit['files'] != expected:
        raise SyncError('all exact source bytes require PUBLIC-SAFE review')
    manifest = {'format': 3, 'publication': 'public-safe', 'channel': channel,
                'owner': ('AlexandrShapkin/project-template' if channel == 'admin'
                          else 'AlexandrShapkin/codex-engineering-kit'),
                'generator': generator_revision, 'review': review_sha256,
                'source': original}
    metadata(manifest, channel, public=True)
    raw = encoded({'manifest': manifest,
                   'contents': {name: value.decode('utf-8') for name, value in contents.items()}})
    if len(raw) > 1024 * 1024:
        raise SyncError('distribution exceeds bundle read limit')
    with location(Path(output).parent, Path(output).name).open('xb') as stream:
        stream.write(raw)
    return {'manifest': manifest, 'candidate_sha256': digest(raw),
            'publication_authorized': False}
