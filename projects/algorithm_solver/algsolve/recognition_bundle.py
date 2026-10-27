"""Bounded, content-addressed index/BITS bundles; no deployment authority.

Operators supply already-authorized input paths and an independently approved,
asset-specific publication grant registry. Hashes prove integrity, not permission,
encoder equivalence, recognition qualification, or source/case access. This module
never acquires descriptions, loads a model, or follows paths inside document data.
"""
from __future__ import annotations

import ast
from contextlib import contextmanager
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import struct
import tempfile

SCHEMA = 'gamma.recognition-bundle.v1'
MAX_FILES = 20000
MAX_FILE_BYTES = 256 * 1024**2
MAX_TOTAL_BYTES = 512 * 1024**2
MAX_JSON_BYTES = 32 * 1024**2
HASH = re.compile(r'[0-9a-f]{64}\Z')
ID = re.compile(r'leetcode:[1-9][0-9]*\Z')
KEY = re.compile(r'(?:leetcode:[1-9][0-9]*|lc:[a-z0-9]+(?:-[a-z0-9]+)*)\Z')
SLUG = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*\Z')
COMPONENT_ROLES = {
    'index_keys': 'index-keys', 'index_vectors': 'index-vectors',
    'documents': 'documents', 'aliases': 'aliases',
    'preprocessing': 'preprocessing', 'runtime': 'runtime',
    'vector_binding': 'vector-binding',
    'bits_catalogue': 'bits-catalogue', 'bits_manifest': 'bits-manifest',
}
PUBLIC_ROLES = {'bits-catalogue', 'bits-manifest', 'bits-packet', 'public-ui'}
ROLES = set(COMPONENT_ROLES.values()) | PUBLIC_ROLES | {'model-manifest'}


class ReleaseMismatch(ValueError):
    """The client/activation expected a different complete release."""


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _unique(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, 'duplicate JSON field')
        result[key] = value
    return result


def _decode(raw):
    _require(len(raw) <= MAX_JSON_BYTES, 'JSON exceeds bundle bound')
    return json.loads(raw, object_pairs_hook=_unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def _relative(name):
    _require(isinstance(name, str) and name and '\\' not in name, 'invalid bundle path')
    parts = name.split('/')
    _require(not name.startswith('/') and all(p not in ('', '.', '..') for p in parts)
             and len(parts) <= 16 and not any(p.startswith('.') for p in parts), 'unsafe bundle path')
    _require(str(PurePosixPath(name)) == name, 'noncanonical bundle path')
    return name


def _regular(root, name):
    """Validate every existing component without following child symlinks."""
    name = _relative(name)
    current = root
    for part in name.split('/'):
        current = current / part
        info = current.lstat()
        _require(not stat.S_ISLNK(info.st_mode), 'symlink in bundle asset path')
        if current != root / name:
            _require(stat.S_ISDIR(info.st_mode), 'non-directory asset path component')
    _require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, 'asset must be a regular unlinked file')
    _require(info.st_size <= MAX_FILE_BYTES, 'asset exceeds bundle bound')
    return current


@contextmanager
def _open_regular(root, name):
    """Open using no-follow directory descriptors, including during races."""
    parts = _relative(name).split('/')
    directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    descriptor = None
    try:
        for part in parts[:-1]:
            successor = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            os.close(directory)
            directory = successor
        descriptor = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory)
        info = os.fstat(descriptor)
        _require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, 'asset must be a regular single-link file')
        _require(info.st_size <= MAX_FILE_BYTES, 'asset exceeds bundle bound')
        with os.fdopen(descriptor, 'rb') as stream:
            descriptor = None
            yield stream
    finally:
        if descriptor is not None:
            os.close(descriptor)
        os.close(directory)


def _sha_file(root, name):
    result = hashlib.sha256()
    with _open_regular(root, name) as stream:
        count = 0
        for block in iter(lambda: stream.read(1024**2), b''):
            count += len(block)
            _require(count <= MAX_FILE_BYTES, 'asset grew beyond bundle bound')
            result.update(block)
    return result.hexdigest()


def _json(root, name, expected=None):
    with _open_regular(root, name) as stream:
        _require(os.fstat(stream.fileno()).st_size <= MAX_JSON_BYTES, 'JSON exceeds bundle bound')
        raw = stream.read(MAX_JSON_BYTES + 1)
    if expected is not None:
        _require(len(raw) == expected['bytes'] and hashlib.sha256(raw).hexdigest() == expected['sha256'],
                 'JSON asset changed while verifying')
    return _decode(raw)


def _expected_identity(actual, expected):
    if expected is not None and actual != expected:
        raise ReleaseMismatch('release identity mismatch')


def _specification(spec):
    _require(isinstance(spec, dict) and set(spec) == {
        'schema', 'ordered_problem_ids', 'vector_dimension', 'components',
        'files', 'publication_permissions'}, 'unexpected bundle specification fields')
    _require(spec['schema'] == SCHEMA, 'unsupported bundle schema')
    ids = spec['ordered_problem_ids']
    _require(isinstance(ids, list) and 0 < len(ids) <= MAX_FILES and
             all(isinstance(pid, str) and ID.fullmatch(pid) for pid in ids) and
             len(ids) == len(set(ids)), 'duplicate or invalid ordered canonical IDs')
    _require(type(spec['vector_dimension']) is int and 0 < spec['vector_dimension'] <= 8192,
             'invalid vector dimension')
    components = spec['components']
    _require(isinstance(components, dict) and set(components) == set(COMPONENT_ROLES) | {'model_manifests'},
             'complete component bindings required')
    files = spec['files']
    _require(isinstance(files, dict) and 0 < len(files) <= MAX_FILES, 'invalid file inventory')
    total = 0
    for name, row in files.items():
        _relative(name)
        _require(name != 'manifest.json', 'manifest cannot describe itself')
        _require(isinstance(row, dict) and set(row) == {'role', 'sha256', 'bytes', 'publication', 'permission_id'},
                 'invalid file descriptor')
        _require(row['role'] in ROLES and isinstance(row['sha256'], str) and HASH.fullmatch(row['sha256']),
                 'invalid file role or hash')
        _require(type(row['bytes']) is int and 0 <= row['bytes'] <= MAX_FILE_BYTES, 'invalid file size')
        total += row['bytes']
        public = name.startswith('public/')
        _require(row['publication'] == ('public' if public else 'private'), 'public path/scope mismatch')
        _require((row['role'] in PUBLIC_ROLES) == public, 'public/private role mismatch')
        _require((isinstance(row['permission_id'], str) and bool(row['permission_id'])) if public
                 else row['permission_id'] is None, 'asset-specific public permission required')
    _require(total <= MAX_TOTAL_BYTES, 'bundle exceeds total byte bound')
    for component, role in COMPONENT_ROLES.items():
        name = components[component]
        _require(isinstance(name, str) and name in files and files[name]['role'] == role,
                 'component path/role missing: ' + component)
    models = components['model_manifests']
    _require(isinstance(models, list) and models and len(models) == len(set(models)) and
             all(isinstance(name, str) and name in files and files[name]['role'] == 'model-manifest'
                 for name in models), 'explicit model manifest bindings required')
    component_paths = [components[k] for k in COMPONENT_ROLES] + models
    _require(len(set(component_paths)) == len(component_paths), 'components cannot share files')
    _require(set(component_paths) == {name for name, row in files.items()
             if row['role'] not in {'bits-packet', 'public-ui'}}, 'unbound private component')
    permissions = spec['publication_permissions']
    used = {row['permission_id'] for row in files.values() if row['publication'] == 'public'}
    _require(isinstance(permissions, dict) and set(permissions) == used and
             all(isinstance(h, str) and HASH.fullmatch(h) for h in permissions.values()),
             'exact publication grant bindings required')


def _permissions(spec, registry):
    """Registry is supplied by the operator, never trusted from the bundle."""
    _require(isinstance(registry, dict), 'operator publication registry required')
    for ident, expected in spec['publication_permissions'].items():
        grant = registry.get(ident)
        _require(isinstance(grant, dict) and set(grant) == {'authority', 'reference', 'scope', 'assets'},
                 'independent publication grant missing')
        _require(all(isinstance(grant[k], str) and grant[k].strip() for k in ('authority', 'reference'))
                 and grant['scope'] == 'public-recognition-assets' and isinstance(grant['assets'], dict),
                 'publication provenance/scope missing')
        _require(digest(grant) == expected, 'publication grant provenance changed')
    for name, row in spec['files'].items():
        if row['publication'] == 'public':
            grant = registry[row['permission_id']]
            _require(grant['assets'].get(name) == row['sha256'], 'public asset not explicitly permitted')


def _inventory(root):
    """Bounded metadata-only walk of this one release, never the source checkout."""
    found = set()
    pending = [(root, 0)]
    examined = 0
    while pending:
        directory, depth = pending.pop()
        _require(depth <= 16, 'release directory depth exceeds bound')
        with os.scandir(directory) as entries:
            for entry in entries:
                examined += 1
                _require(examined <= MAX_FILES * 3, 'release directory entry bound exceeded')
                _require(not entry.is_symlink(), 'symlink in release')
                if entry.is_dir(follow_symlinks=False):
                    pending.append((Path(entry.path), depth + 1))
                else:
                    _require(entry.is_file(follow_symlinks=False), 'special file in release')
                    found.add(Path(entry.path).relative_to(root).as_posix())
                    _require(len(found) <= MAX_FILES + 1, 'release file bound exceeded')
    return found


def _vectors(root, name, rows, dimension, binding_rows, expected_sha256):
    """Stream a bounded C-order little-endian float32 NPY; never unpickle."""
    with _open_regular(root, name) as stream:
        content_hash = hashlib.sha256()
        def read(size):
            raw = stream.read(size)
            content_hash.update(raw)
            return raw
        _require(read(6) == b'\x93NUMPY', 'invalid NPY magic')
        version = read(2)
        _require(version in (b'\x01\x00', b'\x02\x00', b'\x03\x00'), 'unsupported NPY version')
        size_bytes = 2 if version == b'\x01\x00' else 4
        raw_size = read(size_bytes)
        _require(len(raw_size) == size_bytes, 'incomplete NPY header')
        header_size = int.from_bytes(raw_size, 'little')
        _require(0 < header_size <= 65536, 'NPY header exceeds bound')
        raw_header = read(header_size)
        _require(len(raw_header) == header_size, 'incomplete NPY header')
        try:
            header = ast.literal_eval(raw_header.decode('utf-8' if version == b'\x03\x00' else 'latin1'))
        except (ValueError, SyntaxError, RecursionError) as error:
            raise ValueError('invalid NPY header') from error
        _require(isinstance(header, dict) and set(header) == {'descr', 'fortran_order', 'shape'} and
                 header['descr'] == '<f4' and header['fortran_order'] is False and
                 header['shape'] == (rows, dimension), 'NPY dtype/order/dimensions differ')
        for position in range(rows):
            raw = read(4 * dimension)
            _require(len(raw) == 4 * dimension, 'missing vector row')
            _require(hashlib.sha256(raw).hexdigest() == binding_rows[position]['vector_row_sha256'],
                     'vector row/order binding mismatch')
            values = struct.unpack('<' + 'f' * dimension, raw)
            _require(all(math.isfinite(value) for value in values), 'nonfinite vector')
            norm = math.sqrt(math.fsum(value * value for value in values))
            _require(abs(norm - 1) <= 1e-4, 'vector normalization differs')
        _require(read(1) == b'', 'extra vector payload')
        _require(content_hash.hexdigest() == expected_sha256, 'vector file changed while verifying')


def _relations(root, spec):
    components, files = spec['components'], spec['files']
    ids = spec['ordered_problem_ids']
    def read(name):
        return _json(root, name, files[name])
    keys = read(components['index_keys'])
    _require(isinstance(keys, list) and len(keys) == len(ids) and len(set(keys)) == len(keys) and
             all(isinstance(key, str) and KEY.fullmatch(key) for key in keys), 'invalid ordered index keys')
    aliases = read(components['aliases']).get('by_key')
    _require(isinstance(aliases, dict) and [aliases.get(key) for key in keys] == ids and
             all(not key.startswith('leetcode:') or key == pid for key, pid in zip(keys, ids)),
             'canonical alias/index order mismatch')
    documents = read(components['documents']).get('documents')
    _require(isinstance(documents, list) and [row.get('problem_id') for row in documents] == ids,
             'document identity/order mismatch')
    for row in documents:
        text = row.get('text')
        _require(isinstance(text, str) and text and row.get('document_sha256') == hashlib.sha256(text.encode()).hexdigest()
                 and row.get('bytes') == len(text.encode()), 'document bytes/hash mismatch')
    preprocessing = read(components['preprocessing'])
    _require(isinstance(preprocessing, dict) and {'encoder', 'model', 'adapter', 'tokenizer', 'pooling',
             'normalization', 'truncation', 'document_instruction'} <= set(preprocessing),
             'complete preprocessing identity required')
    runtime = read(components['runtime'])
    _require(isinstance(runtime, dict) and runtime, 'runtime identity required')
    for name in components['model_manifests']:
        model = read(name)
        _require(isinstance(model, dict) and model, 'model manifest must be nonempty JSON metadata')
    binding = read(components['vector_binding'])
    _require(isinstance(binding, dict) and set(binding) == {'schema', 'component_sha256', 'rows'} and
             binding['schema'] == 'gamma.recognition-vector-binding.v1', 'vector provenance binding required')
    expected = {name: files[path]['sha256'] for name, path in components.items()
                if name not in ('vector_binding', 'model_manifests', 'bits_catalogue', 'bits_manifest')}
    expected['model_manifests'] = {name: files[name]['sha256'] for name in components['model_manifests']}
    _require(binding['component_sha256'] == expected, 'vector execution/document/component binding mismatch')
    rows = binding['rows']
    _require(isinstance(rows, list) and len(rows) == len(ids), 'vector row provenance missing')
    for pid, doc, row in zip(ids, documents, rows):
        _require(isinstance(row, dict) and set(row) == {'problem_id', 'document_sha256', 'vector_row_sha256',
                 'origin', 'provenance_sha256'} and row['problem_id'] == pid and
                 row['document_sha256'] == doc['document_sha256'] and row['origin'] in ('reused', 'generated') and
                 all(isinstance(row[k], str) and HASH.fullmatch(row[k])
                     for k in ('vector_row_sha256', 'provenance_sha256')), 'invalid vector row provenance')
    _vectors(root, components['index_vectors'], len(ids), spec['vector_dimension'], rows,
             files[components['index_vectors']]['sha256'])
    catalogue_body = read(components['bits_catalogue'])
    _require(isinstance(catalogue_body, dict) and {'problems'} <= set(catalogue_body) <= {'schema', 'problems'},
             'BITS catalogue must contain metadata only')
    catalogue = catalogue_body['problems']
    _require(isinstance(catalogue, list) and len(catalogue) == len(keys), 'BITS catalogue population differs')
    catalogue_keys = [row.get('key') for row in catalogue]
    _require(len(set(catalogue_keys)) == len(catalogue_keys) and set(catalogue_keys) == set(keys),
             'BITS/index keys differ or duplicate')
    catalogue_by_key = {}
    for row in catalogue:
        _require(isinstance(row, dict) and {'key', 'problem_id', 'title', 'slug'} <= set(row) <=
                 {'key', 'problem_id', 'title', 'slug', 'difficulty'}, 'BITS row must contain identity metadata only')
        key, slug = row['key'], row.get('slug')
        _require(row.get('problem_id') == aliases[key] and isinstance(row.get('title'), str) and bool(row['title']),
                 'BITS canonical identity missing')
        if key.startswith('lc:'):
            _require(slug == key[3:], 'legacy key requires its proven exact slug')
        elif slug is not None:
            _require(isinstance(slug, str) and SLUG.fullmatch(slug) and aliases.get('lc:' + slug) == row['problem_id'],
                     'canonical row slug requires independently mapped alias')
        catalogue_by_key[key] = row
    packet_manifest = read(components['bits_manifest'])
    _require(isinstance(packet_manifest, dict) and {'problems'} <= set(packet_manifest) <= {'schema', 'problems'},
             'BITS packet manifest must contain metadata only')
    packets = packet_manifest['problems']
    _require(isinstance(packets, dict) and set(packets) == set(keys),
             'BITS packet manifest keys differ')
    packet_paths = set()
    for key, pid in zip(keys, ids):
        row = packets[key]
        _require(isinstance(row, dict) and row.get('problem_id') == pid, 'packet canonical identity differs')
        if row.get('scope') == 'metadata-only':
            _require(set(row) == {'problem_id', 'scope'}, 'metadata-only identity must not name a payload')
            continue
        _require(set(row) == {'problem_id', 'scope', 'path', 'sha256'} and row['scope'] == 'public-statement',
                 'explicit packet scope required')
        path = row['path']
        _require(path in files and files[path]['role'] == 'bits-packet' and files[path]['sha256'] == row['sha256']
                 and path not in packet_paths, 'packet file/hash mapping differs')
        packet_paths.add(path)
        packet = read(path)
        _require(isinstance(packet, dict) and set(packet) == {'schema', 'problem'} and
                 packet['schema'] == 'gamma.bits-public-statement.v1', 'solution guides/cases are not packet assets')
        problem = packet['problem']
        _require(isinstance(problem, dict) and set(problem) == {'problem_id', 'key', 'slug', 'title', 'statement'} and
                 problem['problem_id'] == pid and problem['key'] == key and
                 problem['slug'] == catalogue_by_key[key].get('slug') and
                 isinstance(problem['title'], str) and isinstance(problem['statement'], str),
                 'packet identity or statement-only scope differs')
    _require(packet_paths == {name for name, row in files.items() if row['role'] == 'bits-packet'},
             'unreferenced public packet')


def _verify(directory, expected_release_id, publication_permissions, *, content_addressed=True):
    root = Path(directory).resolve(strict=True)
    manifest = _json(root, 'manifest.json')
    _require(isinstance(manifest, dict) and 'release_id' in manifest, 'release identity required')
    release_id = manifest['release_id']
    spec = {key: value for key, value in manifest.items() if key != 'release_id'}
    _specification(spec)
    _require(isinstance(release_id, str) and HASH.fullmatch(release_id) and digest(spec) == release_id,
             'release manifest identity differs')
    _expected_identity(release_id, expected_release_id)
    if content_addressed:
        _require(root.name == release_id, 'release directory is not content-addressed')
    # Authorization checks precede every listed public payload open.
    _permissions(spec, publication_permissions)
    _require(_inventory(root) == set(spec['files']) | {'manifest.json'}, 'unlisted or missing release assets')
    for name, row in spec['files'].items():
        path = _regular(root, name)
        _require(path.stat().st_size == row['bytes'] and _sha_file(root, name) == row['sha256'],
                 'asset size/hash mismatch: ' + name)
    _relations(root, spec)
    return manifest


def verify_release(directory, *, expected_release_id=None, publication_permissions):
    """Verify a complete immutable candidate; this does not approve its use."""
    return _verify(directory, expected_release_id, publication_permissions)


def prepare_release(source_root, releases_root, specification, *, publication_permissions):
    """Copy only explicit pre-authorized inputs into a new content-addressed bundle.

    The operator must validate description acquisition/use and vector lineage
    before calling. This verifies their exact bindings; it cannot invent lineage.
    Existing complete bundles are verified and reused, never overwritten.
    """
    spec = _decode(encoded(specification))
    _specification(spec)
    _permissions(spec, publication_permissions)
    release_id = digest(spec)
    source = Path(source_root).resolve(strict=True)
    destination = Path(releases_root)
    destination.mkdir(parents=True, exist_ok=True)
    destination = destination.resolve(strict=True)
    target = destination / release_id
    if target.exists():
        verify_release(target, expected_release_id=release_id, publication_permissions=publication_permissions)
        return target
    stage = Path(tempfile.mkdtemp(prefix='.stage-', dir=destination))
    try:
        for name, row in spec['files'].items():
            original = _regular(source, name)
            _require(original.stat().st_size == row['bytes'], 'source asset size changed')
            output = stage / name
            output.parent.mkdir(parents=True, exist_ok=True)
            with _open_regular(source, name) as incoming, output.open('xb') as outgoing:
                _require(os.fstat(incoming.fileno()).st_size == row['bytes'], 'source asset size changed before copy')
                result = hashlib.sha256()
                count = 0
                while block := incoming.read(1024**2):
                    count += len(block)
                    _require(count <= row['bytes'], 'source asset grew during copy')
                    result.update(block)
                    outgoing.write(block)
                _require(count == row['bytes'] and result.hexdigest() == row['sha256'], 'source asset hash changed')
                outgoing.flush()
                os.fsync(outgoing.fileno())
        manifest = dict(spec, release_id=release_id)
        with (stage / 'manifest.json').open('xb') as stream:
            stream.write(encoded(manifest) + b'\n')
            stream.flush()
            os.fsync(stream.fileno())
        _verify(stage, release_id, publication_permissions, content_addressed=False)
        # Rename is atomic. Concurrent same-identity publication never replaces content.
        try:
            stage.rename(target)
        except FileExistsError:
            verify_release(target, expected_release_id=release_id, publication_permissions=publication_permissions)
        _fsync_directory(destination)
        return target
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def _fsync_directory(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


@contextmanager
def _state_lock(state_root):
    root = Path(state_root)
    root.mkdir(parents=True, exist_ok=True)
    root = root.resolve(strict=True)
    descriptor = os.open(root / '.activation.lock', os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield root
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def _pointer(root):
    path = root / 'active.json'
    if not path.exists():
        return None
    pointer = _json(root, 'active.json')
    _require(isinstance(pointer, dict) and set(pointer) == {'schema', 'current', 'previous'} and
             pointer['schema'] == 'gamma.recognition-active-release.v1', 'invalid active pointer')
    for kind in ('current', 'previous'):
        value = pointer[kind]
        if value is None:
            _require(kind == 'previous', 'current release required')
        else:
            _require(isinstance(value, dict) and set(value) == {'release_id', 'directory'} and
                     isinstance(value['release_id'], str) and HASH.fullmatch(value['release_id']) and
                     isinstance(value['directory'], str) and Path(value['directory']).is_absolute(),
                     'invalid release pointer entry')
    return pointer


def _verify_entry(entry, permissions):
    return verify_release(entry['directory'], expected_release_id=entry['release_id'],
                          publication_permissions=permissions)


def _write_pointer(root, value):
    descriptor, filename = tempfile.mkstemp(prefix='.active-', dir=root)
    temporary = Path(filename)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(encoded(value) + b'\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, root / 'active.json')
        _fsync_directory(root)
    finally:
        temporary.unlink(missing_ok=True)


def activate_release(state_root, release_directory, *, expected_current_release_id, publication_permissions):
    """Atomic compare-and-swap of the complete bundle; explicit operator action.

    This only changes a local pointer. A serving owner must authorize activation
    and consume this one pointer for both index and BITS assets. No service is
    started/restarted, no hosting is changed, and no deployment is implied.
    """
    with _state_lock(state_root) as root:
        pointer = _pointer(root)
        current = pointer['current'] if pointer else None
        actual = current['release_id'] if current else None
        if actual != expected_current_release_id:
            raise ReleaseMismatch('active release changed before activation')
        manifest = verify_release(release_directory, publication_permissions=publication_permissions)
        if current:
            _verify_entry(current, publication_permissions)
        if actual == manifest['release_id']:
            return pointer
        entry = {'release_id': manifest['release_id'], 'directory': str(Path(release_directory).resolve(strict=True))}
        successor = {'schema': 'gamma.recognition-active-release.v1', 'current': entry, 'previous': current}
        _write_pointer(root, successor)
        return successor


def rollback_release(state_root, *, expected_current_release_id, publication_permissions):
    """One operation restores both previous index and BITS by swapping the pointer."""
    with _state_lock(state_root) as root:
        pointer = _pointer(root)
        if pointer is None or pointer['current']['release_id'] != expected_current_release_id:
            raise ReleaseMismatch('active release changed before rollback')
        _require(pointer['previous'] is not None, 'no previous complete release retained')
        # The current candidate may be corrupt: restoring a verified predecessor
        # must not require the broken candidate to verify successfully.
        _verify_entry(pointer['previous'], publication_permissions)
        successor = dict(pointer, current=pointer['previous'], previous=pointer['current'])
        _write_pointer(root, successor)
        return successor


def resolve_active_release(state_root, *, expected_release_id=None, publication_permissions):
    """Read the pointer once and return a single verified static/index snapshot.

    Servers must use this same returned directory for every component of the
    request. Compare a client's release ID before model execution; do not resolve
    the pointer separately for the index and static assets.
    """
    root = Path(state_root).resolve(strict=True)
    pointer = _pointer(root)
    _require(pointer is not None, 'no active release')
    entry = pointer['current']
    _expected_identity(entry['release_id'], expected_release_id)
    manifest = _verify_entry(entry, publication_permissions)
    directory = Path(entry['directory']).resolve(strict=True)
    return {'release_id': entry['release_id'], 'directory': directory,
            'public_root': directory / 'public', 'components': {
                key: ([directory / path for path in value] if isinstance(value, list) else directory / value)
                for key, value in manifest['components'].items()}, 'manifest': manifest}
