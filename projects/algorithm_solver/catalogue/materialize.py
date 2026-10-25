"""Bounded, metadata-first exact source reads; no full-corpus loader or execution.

The caller supplies an independently authorized immutable locator manifest and
access policy. This adapter verifies bindings, not the authority granting access.
A successful read is not current-runtime qualification or a serving release.
"""
import hashlib
import os
from pathlib import PurePosixPath


def read_source(selection, locator, policy, *, maximum_bytes=1_048_576):
    """Check problem authorization and source identity BEFORE opening any path."""
    for key in ('authorized_problem_ids', 'protected_problem_ids'):
        ids = policy.get(key)
        if not isinstance(ids, list) or any(not isinstance(x, str) or not x for x in ids) or len(ids) != len(set(ids)):
            raise ValueError('access-policy identities must be explicit unique lists')
    if selection.get('status') != 'selected':
        raise ValueError('a qualified consumer selection is required')
    pid, language = selection.get('problem_id'), selection.get('language')
    if not isinstance(pid, str) or language not in ('javascript', 'python'):
        raise ValueError('invalid selected identity')
    if pid in policy['protected_problem_ids'] or pid not in policy['authorized_problem_ids']:
        raise PermissionError('problem source access is not authorized')
    impl = selection['implementation']
    if impl.get('status') != 'qualified':
        raise ValueError('pending or compatibility-only source cannot be served')
    if locator.get('problem_id') != pid or locator.get('language') != language:
        raise ValueError('source locator identity mismatch')
    for key in ('source_sha256', 'receipt_sha256'):
        if locator.get(key) != impl.get(key):
            raise ValueError('source locator qualification binding mismatch')
    if locator.get('universe_sha256') != policy['universe_sha256']:
        raise ValueError('locator access-universe drift')
    root = policy['source_root']
    relative = locator.get('relative_path')
    if not isinstance(relative, str) or not relative or '\\' in relative:
        raise ValueError('invalid relative source path')
    parts = relative.split('/')
    if PurePosixPath(relative).is_absolute() or any(p in ('', '.', '..') for p in parts):
        raise ValueError('source path escapes approved root')
    if not isinstance(maximum_bytes, int) or not 0 < maximum_bytes <= 16_777_216:
        raise ValueError('bounded source size required')
    # Each child is opened without following symlinks. Directory handles avoid
    # a path-replacement race between checking components and opening the file.
    directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            os.close(directory); directory = child
        fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        try:
            import stat
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise ValueError('source must be a regular file')
            with os.fdopen(fd, 'rb', closefd=False) as source:
                data = source.read(maximum_bytes + 1)
            if len(data) > maximum_bytes:
                raise ValueError('source exceeds frozen materialization bound')
        finally:
            os.close(fd)
    finally:
        os.close(directory)
    if hashlib.sha256(data).hexdigest() != impl['source_sha256']:
        raise ValueError('source bytes changed since qualification')
    return data
