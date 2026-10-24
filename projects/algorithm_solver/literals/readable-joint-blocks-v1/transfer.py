#!/usr/bin/env python3
"""Transfer only the pinned, exposed 300-fit/100-development-validation inputs.

This utility never runs candidates or qualifies a milestone. The exporter reads
the one hash-pinned population metadata file, emits only allowed rows, and opens
only explicitly allowlisted source/case/baseline files. No recursive scan occurs.
The importer requires the archive hash obtained from the trusted export receipt;
the filtered metadata cannot independently prove its membership in a SHA256-only
commitment to the complete original metadata file.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tarfile
import tempfile

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[3]
SOURCE_COMMIT = '2fb7c7391832d2a2dfdef7f1b1f0752359926596'
SOURCE_CONTRACT = 'projects/algorithm_solver/literals/cost-decomposition-v1/contract.json'
QUALIFICATION_CONTRACT = 'projects/algorithm_solver/literals/name-search-v1/contract.json'
CONTRACT_PINS = {
    SOURCE_CONTRACT: 'a2c501792e4ef369a1f2630fd4ffd3b6623c1146ca3d7aac7115b469efe8cd61',
    QUALIFICATION_CONTRACT: '3e4dcd8f182a5965a14e414433bf798274752c7ce64b98b6729fee79561789c6',
}
SUBSET = 'population400/manifest.json'
RECEIPT = 'transfer-receipt.json'
MAX_FILE = 32 * 1024 * 1024
MAX_TOTAL = 512 * 1024 * 1024
HEX = re.compile(r'[0-9a-f]{64}\Z')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate JSON key')
        result[key] = value
    return result


def parse(raw):
    return json.loads(raw, object_pairs_hook=_pairs)


def packed(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + '\n').encode()


def relative(name):
    require(isinstance(name, str) and name and '\\' not in name, 'invalid relative path')
    p = PurePosixPath(name)
    require(not p.is_absolute() and str(p) == name and all(x not in ('.', '..') for x in p.parts),
            'unsafe relative path')
    return p.parts


def _root_fd(path):
    """Walk absolute components without following even an intermediate symlink."""
    p = Path(os.path.abspath(path))
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in p.parts[1:]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        return fd
    except BaseException:
        os.close(fd)
        raise


def read_relative(root, name, maximum=MAX_FILE):
    """Descriptor-relative O_NOFOLLOW prevents parent/final symlink races."""
    parts = relative(name)
    fd = _root_fd(root)
    try:
        for part in parts[:-1]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        child = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        with os.fdopen(child, 'rb') as stream:
            info = os.fstat(stream.fileno())
            require(stat.S_ISREG(info.st_mode) and info.st_size <= maximum, 'not a bounded regular file')
            raw = stream.read(maximum + 1)
            require(len(raw) <= maximum, 'file exceeds size limit')
            return raw
    finally:
        os.close(fd)


def derive_manifest(repository=REPO_ROOT):
    """Derive in memory from local public contracts; never fetch or accept drift."""
    contracts = {}
    for name, expected in CONTRACT_PINS.items():
        raw = read_relative(repository, name)
        require(sha(raw) == expected, 'pinned repository contract hash mismatch: ' + name)
        contracts[name] = parse(raw)
    sources, qualification = contracts[SOURCE_CONTRACT], contracts[QUALIFICATION_CONTRACT]
    files = []
    for row in sources['sources']:
        files.append({'path': row['relative_path'], 'sha256': row['sha256'],
                      'kind': 'source', 'id': row['id']})
    for row in qualification['qualification']:
        for name, digest in row['files'].items():
            files.append({'path': name, 'sha256': digest,
                          'kind': 'cases' if name.endswith('-tests.json') else 'baseline', 'id': row['id']})
    for width, row in sources['dictionaries'].items():
        files.append({'path': row['relative_path'], 'sha256': row['sha256'],
                      'kind': 'dictionary', 'width': 2 ** int(width)})
    return {
        'schema': 'gamma.dot.development400-transfer.v1', 'source_commit': SOURCE_COMMIT,
        'partition': sources['partition'],
        'population_metadata': {'path': 'population500/manifest.json',
                                'sha256': qualification['manifest_sha256']},
        'provenance': dict(CONTRACT_PINS),
        'scope': 'Exactly exposed 300 fit and 100 consumed development-validation programs. No final-heldout100 or protected66 payload files. No sources, cases, baselines or dictionary contents in this metadata-only manifest.',
        'files': sorted(files, key=lambda row: row['path']),
    }


def load_manifest(path=None):
    # The optional path is for caller-supplied synthetic test fixtures. The CLI
    # always derives its policy from the pinned repository contracts above.
    if path is None:
        spec = derive_manifest()
        raw = (json.dumps(spec, indent=2) + '\n').encode()
    else:
        path = Path(path).absolute()
        raw = read_relative(path.parent, path.name)
        spec = parse(raw)
    require(spec.get('schema') == 'gamma.dot.development400-transfer.v1', 'manifest schema')
    partition = spec['partition']
    fit, validation = partition['dev_fit'], partition['dev_val']
    require(all(type(x) is int and x > 0 for x in fit + validation), 'invalid problem ID')
    require(len(fit) == 300 and len(validation) == 100 and len(set(fit + validation)) == 400,
            'exact disjoint 300/100 partition required')
    allowed = set(fit + validation)
    files = spec['files']
    require(len(files) == 1202, 'exact 1202-file payload required')
    seen = set()
    kinds = {'source': set(), 'cases': set(), 'baseline': set(), 'dictionary': set()}
    for row in files:
        name = row['path']
        relative(name)
        require(name not in seen and HEX.fullmatch(row['sha256']), 'duplicate path or invalid hash')
        seen.add(name)
        kind = row['kind']
        require(kind in kinds, 'unknown payload kind')
        if kind == 'dictionary':
            width = row['width']
            require(width in (128, 256) and name == f'roles/run-v1/dictionaries/L-R-{width}.json',
                    'unexpected dictionary path')
            kinds[kind].add(width)
        else:
            pid = row['id']
            require(type(pid) is int and pid in allowed, 'file outside allowed partition')
            candidates = {
                'source': (f'style150/submitted/{pid}.js', f'scale500/submitted/{pid}.js'),
                'cases': (f'population500/{pid}-tests.json',),
                'baseline': (f'population500-baseline/qualification/baselines/{pid}.json',),
            }
            require(name in candidates[kind] and pid not in kinds[kind], 'unexpected or duplicate identity')
            kinds[kind].add(pid)
    require(all(kinds[k] == allowed for k in ('source', 'cases', 'baseline'))
            and kinds['dictionary'] == {128, 256}, 'incomplete payload')
    require(spec['population_metadata']['path'] == 'population500/manifest.json'
            and HEX.fullmatch(spec['population_metadata']['sha256']), 'metadata commitment')
    return spec, sha(raw)


def filtered_metadata(raw, spec):
    require(sha(raw) == spec['population_metadata']['sha256'], 'population metadata hash mismatch')
    original = parse(raw)
    allowed = set(spec['partition']['dev_fit'] + spec['partition']['dev_val'])
    selected = {}
    tests = {r['id']: r['sha256'] for r in spec['files'] if r['kind'] == 'cases'}
    for row in original['rows']:
        pid = row.get('id')
        require(type(pid) is int, 'metadata ID must be integer')
        if pid not in allowed:
            continue
        require(pid not in selected and row.get('tests_sha256') == tests[pid], 'metadata duplicate or case hash')
        selected[pid] = row
    require(set(selected) == allowed, 'missing allowed metadata')
    return {
        'schema': 'gamma.dot.filtered-development-metadata.v1', 'problems': 400,
        'source_metadata_sha256': spec['population_metadata']['sha256'],
        'rows': [selected[k] for k in sorted(selected)],
        'filtered': True,
        'provenance': 'Exporter checked original metadata hash; importer authenticates this subset via trusted archive SHA256.',
    }


def _add(archive, name, raw):
    info = tarfile.TarInfo(name)
    info.size = len(raw)
    info.mode = 0o600
    info.mtime = 0
    archive.addfile(info, io.BytesIO(raw))


def export_inputs(work, archive_path, manifest=None):
    spec, manifest_hash = load_manifest(manifest)
    metadata = packed(filtered_metadata(read_relative(work, spec['population_metadata']['path']), spec))
    receipt = packed({
        'schema': 'gamma.dot.transfer-receipt.v1', 'manifest_sha256': manifest_hash,
        'source_metadata_sha256': spec['population_metadata']['sha256'],
        'filtered_metadata_sha256': sha(metadata), 'payload_files': len(spec['files']),
        'partition': spec['partition'], 'candidate_execution': False,
        'final_heldout_payload_files_opened': 0, 'protected_payload_files_opened': 0,
    })
    require(len(metadata) <= MAX_FILE and len(receipt) <= MAX_FILE,
            'generated metadata or receipt exceeds file limit')
    target = Path(archive_path).absolute()
    parent_fd = _root_fd(target.parent)
    os.close(parent_fd)
    require(not target.exists() and not target.is_symlink(), 'archive destination exists')
    total = len(metadata) + len(receipt)
    require(total <= MAX_TOTAL, 'payload exceeds total limit')
    descriptor, temporary = tempfile.mkstemp(prefix='.gamma-transfer-', dir=target.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            with tarfile.open(fileobj=stream, mode='w') as archive:
                for row in sorted(spec['files'], key=lambda r: r['path']):
                    raw = read_relative(work, row['path'])
                    require(sha(raw) == row['sha256'], 'payload hash mismatch: ' + row['path'])
                    total += len(raw)
                    require(total <= MAX_TOTAL, 'payload exceeds total limit')
                    _add(archive, row['path'], raw)
                _add(archive, SUBSET, metadata)
                _add(archive, RECEIPT, receipt)
        # Hard-link publication is exclusive: unlike rename, it cannot overwrite.
        os.link(temporary, target)
        return {'archive': str(target), 'sha256': sha(Path(temporary).read_bytes()),
                'payload_files': 1202, 'metadata_rows': 400}
    finally:
        os.unlink(temporary)


def import_inputs(archive_path, destination, archive_sha256, manifest=None):
    spec, manifest_hash = load_manifest(manifest)
    require(isinstance(archive_sha256, str) and HEX.fullmatch(archive_sha256), 'trusted archive SHA256 required')
    archive_path = Path(archive_path).absolute()
    raw_archive = read_relative(archive_path.parent, archive_path.name, MAX_TOTAL + 4 * 1024 * 1024)
    require(sha(raw_archive) == archive_sha256, 'archive hash mismatch')
    expected = {r['path']: r['sha256'] for r in spec['files']}
    expected_names = set(expected) | {SUBSET, RECEIPT}
    payload = {}
    total = 0
    with tarfile.open(fileobj=io.BytesIO(raw_archive), mode='r:') as archive:
        for item in archive:
            relative(item.name)
            require(item.name in expected_names and item.name not in payload, 'extra or duplicate archive member')
            require(item.type == tarfile.REGTYPE and not item.pax_headers and 0 <= item.size <= MAX_FILE,
                    'archive member is not a bounded plain file')
            total += item.size
            require(total <= MAX_TOTAL, 'archive payload too large')
            data = archive.extractfile(item).read(MAX_FILE + 1)
            require(len(data) == item.size, 'truncated archive member')
            if item.name in expected:
                require(sha(data) == expected[item.name], 'payload hash mismatch: ' + item.name)
            payload[item.name] = data
        require(not any(raw_archive[archive.offset:]), 'nonzero archive trailer')
    require(set(payload) == expected_names, 'archive missing allowed members')
    receipt, metadata = parse(payload[RECEIPT]), parse(payload[SUBSET])
    require(receipt.get('schema') == 'gamma.dot.transfer-receipt.v1'
            and receipt['manifest_sha256'] == manifest_hash
            and receipt['source_metadata_sha256'] == spec['population_metadata']['sha256']
            and receipt['filtered_metadata_sha256'] == sha(payload[SUBSET])
            and receipt['partition'] == spec['partition'], 'receipt mismatch')
    ids = [r['id'] for r in metadata['rows']]
    require(metadata.get('schema') == 'gamma.dot.filtered-development-metadata.v1'
            and metadata.get('filtered') is True and metadata.get('problems') == 400
            and metadata.get('source_metadata_sha256') == spec['population_metadata']['sha256']
            and all(type(pid) is int for pid in ids)
            and len(ids) == 400 and len(set(ids)) == 400
            and set(ids) == set(spec['partition']['dev_fit'] + spec['partition']['dev_val']),
            'filtered metadata partition mismatch')
    tests = {r['id']: r['sha256'] for r in spec['files'] if r['kind'] == 'cases'}
    require(all(r.get('tests_sha256') == tests[r['id']] for r in metadata['rows']), 'filtered case hash mismatch')
    target = Path(destination).absolute()
    parent_fd = _root_fd(target.parent)
    os.close(parent_fd)
    require(not target.exists() and not target.is_symlink(), 'destination exists')
    # mkdir is exclusive. On failure remove only this new destination.
    target.mkdir(mode=0o700)
    try:
        for name, data in sorted(payload.items()):
            path = target.joinpath(*relative(name))
            path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            with path.open('xb') as stream:
                stream.write(data)
            path.chmod(0o600)
    except BaseException:
        shutil.rmtree(target)
        raise
    return {'destination': str(target), 'archive_sha256': archive_sha256,
            'payload_files_verified': 1202, 'metadata_rows': 400, 'candidate_execution': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    export = commands.add_parser('export')
    export.add_argument('--work', type=Path, required=True)
    export.add_argument('--archive', type=Path, required=True)
    load = commands.add_parser('import')
    load.add_argument('--archive', type=Path, required=True)
    load.add_argument('--archive-sha256', required=True)
    load.add_argument('--destination', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'export':
        result = export_inputs(args.work, args.archive)
    else:
        result = import_inputs(args.archive, args.destination, args.archive_sha256)
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
