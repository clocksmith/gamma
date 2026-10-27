"""One freshly authorized, identity-bound local source or statement read.

The caller must already hold approval for the exact locator and expected pins;
hash equality is not approval. Boundary metadata paths and trust anchors are
operator inputs, never authority supplied by a payload. This wrapper adds no
policy, registry, cache, fetcher or execution permission. New consumers must pin
this helper and its existing owners explicitly; historical receipts stay intact.
"""
import hashlib
import os
from pathlib import Path
import re

from . import boundary_policy
from . import public_batch_adapter


class PayloadIdentityError(ValueError):
    """A completed read failed identity checks; receipt contains no payload."""

    def __init__(self, receipt):
        super().__init__('payload identity mismatch: ' + ', '.join(receipt['mismatches']))
        self.receipt = receipt


def _local_path(value):
    if not isinstance(value, (str, Path)):
        raise ValueError('an exact local path is required')
    path = os.fspath(value)
    if (not isinstance(path, str) or not path.startswith('/') or '\0' in path or
            any(part in ('', '.', '..') for part in path[1:].split('/'))):
        raise ValueError('an absolute canonical local file path is required')
    return path


def _digest(value, length):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{%d}' % length, value, re.ASCII) is not None


def read_payload(path, *, problem_id, language, payload_kind, artifact_paths,
                 trusted_hashes, expected_sha256, maximum_bytes,
                 expected_size=None, expected_git_blob_oid=None):
    """Return ``(raw_bytes, receipt)`` after one live gate and one bounded read.

    Only the existing six metadata artifacts are read by the policy owner. Its
    decision immediately precedes the existing anchored, no-follow regular-file
    reader. That reader rejects symlinks in every component, special files,
    oversize files and observed changes during the read. No retry or second
    payload read occurs, including on an identity mismatch. All payload digests
    and lengths below derive solely from the returned bytes, never a reopen.

    ``maximum_bytes`` is mandatory: callers retain their already approved bound,
    not a new runtime limit. Path/identity shape checks happen before any open.
    This does not replace the caller's original service/config checks or approval
    of the exact source/statement locator and its independently expected pins.
    """
    path = _local_path(path)
    if (not isinstance(problem_id, str) or
            re.fullmatch(r'leetcode:[1-9][0-9]*', problem_id, re.ASCII) is None or
            not isinstance(language, str) or language not in boundary_policy.LANGUAGES or
            not isinstance(payload_kind, str) or payload_kind not in ('source', 'statement')):
        raise ValueError('exact canonical identity, language and payload kind required')
    if (type(artifact_paths) is not dict or type(trusted_hashes) is not dict or
            set(artifact_paths) != boundary_policy.ARTIFACTS or
            set(trusted_hashes) != boundary_policy.ARTIFACTS):
        raise ValueError('all six existing boundary artifact paths and anchors are required')
    paths = {name: _local_path(value) for name, value in artifact_paths.items()}
    pins = dict(trusted_hashes)
    if any(not _digest(value, 64) for value in pins.values()):
        raise ValueError('invalid boundary SHA-256 anchor')
    if (not _digest(expected_sha256, 64) or
            type(maximum_bytes) is not int or not 0 < maximum_bytes <= 64 * 1024**2 or
            (expected_size is not None and
             (type(expected_size) is not int or not 0 <= expected_size <= maximum_bytes)) or
            (expected_git_blob_oid is not None and not _digest(expected_git_blob_oid, 40))):
        raise ValueError('valid expected payload identities and existing bounded size are required')

    decision = boundary_policy.authorize_before_open(
        problem_id, paths, pins, language=language, payload_kind=payload_kind)
    if (not isinstance(decision, dict) or decision.get('authorized') is not True or
            decision.get('problem_id') != problem_id or decision.get('language') != language or
            decision.get('payload_kind') != payload_kind):
        raise PermissionError('live policy decision does not authorize this exact read')
    raw = public_batch_adapter.bounded_regular_read(path, maximum_bytes=maximum_bytes)

    actual_sha256 = hashlib.sha256(raw).hexdigest()
    actual_oid = hashlib.sha1(b'blob ' + str(len(raw)).encode('ascii') + b'\0' + raw).hexdigest()
    mismatches = []
    if actual_sha256 != expected_sha256:
        mismatches.append('sha256')
    if expected_size is not None and len(raw) != expected_size:
        mismatches.append('bytes')
    if expected_git_blob_oid is not None and actual_oid != expected_git_blob_oid:
        mismatches.append('git_blob_oid')
    receipt = {
        'schema': 'gamma.gated-payload-read.v1',
        'problem_id': problem_id, 'language': language, 'payload_kind': payload_kind,
        'path': path, 'sha256': actual_sha256, 'bytes': len(raw), 'git_blob_oid': actual_oid,
        'expected': {'sha256': expected_sha256, 'bytes': expected_size,
                     'git_blob_oid': expected_git_blob_oid},
        'maximum_bytes': maximum_bytes, 'gate': dict(decision),
        'identity_verified': not mismatches, 'mismatches': mismatches,
        'payload_read_count': 1, 'candidate_executions': 0,
        'semantic_qualification_created': False, 'source_publication_authorized': False,
    }
    if mismatches:
        raise PayloadIdentityError(receipt)
    return raw, receipt
