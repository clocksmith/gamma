"""Import owner-downloaded W002 candidates without generating or executing code."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import stat
import zipfile
from pathlib import Path

MAX_ARCHIVE = 8 * 1024 * 1024
MAX_FILE = 2 * 1024 * 1024
SEMANTICS = ('source_origin', 'normalization', 'numeric_semantics',
             'mutation_contract', 'interface_support', 'input_domain')


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value: object) -> None:
    with path.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write('\n')


def checked_zip(path: Path, wrapper: str | None = None) -> dict[str, bytes]:
    """Flat, bounded regular files only; never call extractall or follow links."""
    if path.stat().st_size > MAX_ARCHIVE:
        raise ValueError('archive exceeds size limit')
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        if len(entries) > 128 or sum(e.file_size for e in entries) > MAX_ARCHIVE:
            raise ValueError('archive expansion exceeds limits')
        files = {}
        layout = None
        for entry in entries:
            name = entry.filename
            parts = name.split('/')
            if wrapper and len(parts) == 2 and parts[0] == wrapper:
                current_layout = 'wrapped'
                name = parts[1]
            else:
                current_layout = 'flat'
            if layout is not None and current_layout != layout:
                raise ValueError('mixed flat and wrapped archive layout')
            layout = current_layout
            kind = stat.S_IFMT(entry.external_attr >> 16)
            if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', name):
                raise ValueError(f'unsafe or nested archive name: {name!r}')
            if name.casefold() in {n.casefold() for n in files}:
                raise ValueError(f'duplicate archive name: {name}')
            if entry.is_dir() or kind not in (0, stat.S_IFREG) or entry.flag_bits & 1:
                raise ValueError(f'nonregular or encrypted member: {name}')
            if entry.file_size > MAX_FILE:
                raise ValueError(f'oversized member: {name}')
            files[name] = archive.read(entry)  # Also checks ZIP CRC.
        return files


def verify_files(files: dict[str, bytes], expected: dict) -> list[dict]:
    assignments = json.loads(files['assignment.json'])
    listing = assignments.get('schema') == 'gamma-js-assignment-listing/v1'
    entries = 'entries' in assignments
    if assignments.get('batch_id' if listing or entries else 'batch') != expected['batch_id']:
        raise ValueError('wrong delivery batch identity')
    rows = assignments['entries' if entries else 'problems' if listing else 'assigned']
    ids = [r['id'] for r in rows]
    wanted = [r['id'] for r in expected['problems']]
    if len(ids) != 25 or len(set(ids)) != 25 or set(ids) != set(wanted):
        raise ValueError('IDs differ from the frozen 25-problem assignment')
    checksum_file = 'SHA256SUMS.txt' if entries else 'SHA256SUMS'
    allowed = {'assignment.json', checksum_file} | (
        {'assignment.txt', 'validation-report.json', 'validation-report.md'} if entries else
        {'VALIDATION.md', 'validation-results.json'} if listing else
        {'validation-report.json', 'validation-examples.json'})
    for number in wanted:
        allowed.update((f'{number:04d}.js', f'{number:04d}-semantics.json'))
    if set(files) != allowed:
        raise ValueError(f'missing/extra files: {sorted(set(files) ^ allowed)}')
    checksums = {}
    for line in files[checksum_file].decode('utf-8').splitlines():
        match = re.fullmatch(r'([0-9a-f]{64})  ([A-Za-z0-9][A-Za-z0-9_.-]*)', line)
        if not match or match[2] in checksums:
            raise ValueError('malformed or duplicate checksum entry')
        checksums[match[2]] = match[1]
    if set(checksums) != set(files) - {checksum_file}:
        raise ValueError('checksum coverage differs from delivered files')
    if any(sha(files[name]) != digest for name, digest in checksums.items()):
        raise ValueError('delivered SHA256 mismatch')
    results = []
    for row in rows:
        number = row['id']
        source, semantics = f'{number:04d}.js', f'{number:04d}-semantics.json'
        if row['javascript_file' if entries else 'source_file' if listing else 'source'] != source or row['semantics_file' if listing or entries else 'semantics'] != semantics:
            raise ValueError(f'file mapping mismatch for {number}')
        declaration = json.loads(files[semantics])
        if not all(isinstance(declaration.get(k), str) and declaration[k].strip() for k in SEMANTICS):
            raise ValueError(f'incomplete semantics declaration for {number}')
        packet = next(p for p in expected['problems'] if p['id'] == number)
        signature = packet['entry']['method'] + '(' + ', '.join(p[0] for p in packet['params']) + ')'
        issues = []
        reported_signature = re.sub(r'^function\s+', '', row['signature'])
        if re.sub(r'\s+', '', reported_signature) != re.sub(r'\s+', '', signature):
            issues.append('delivery manifest signature differs from assignment')
        text = files[source].decode('utf-8')
        # This is an explicit shape diagnostic, not a JavaScript parser or approval.
        if not re.search(r'\bclass\s+Solution\b', text):
            issues.append('assignment requires class Solution; delivered free function')
        results.append({'id': number, 'key': packet['key'], 'source_sha256': sha(files[source]),
                        'semantics_sha256': sha(files[semantics]), 'contract_issues': issues})
    return results


def import_delivery(archive: Path, folder: Path, authority: Path, lane: Path, batch: str) -> dict:
    if not re.fullmatch(r'W002-B\d{2}', batch):
        raise ValueError('invalid batch')
    if archive.is_symlink() or not archive.is_file() or archive.stat().st_size > MAX_ARCHIVE:
        raise ValueError('delivery archive must be a bounded regular file')
    raw = archive.read_bytes()
    digest = sha(raw)
    retained = lane / 'runs' / 'web-deliveries' / batch / digest
    retained.mkdir(parents=True, exist_ok=False)  # Re-import cannot overwrite evidence.
    (retained / 'original.zip').write_bytes(raw)
    receipt = {'schema': 'algsolve.web-delivery.v1', 'batch': batch, 'zip_sha256': digest,
               'archive': str(archive), 'folder': str(folder), 'status': 'received',
               'qualified': False, 'source_regenerated': False, 'rows': []}
    try:
        manifest_bytes = (authority / 'manifest.json').read_bytes()
        manifest_hash = (authority / 'manifest.sha256').read_text().split()[0]
        if sha(manifest_bytes) != manifest_hash:
            raise ValueError('assignment manifest hash mismatch')
        manifest = json.loads(manifest_bytes)
        assigned = next(row for row in manifest['batches'] if row['batch_id'] == batch)
        packet_bytes = (authority / f'{batch}.json').read_bytes()
        if sha(packet_bytes) != assigned['json_sha256']:
            raise ValueError('assignment packet hash mismatch')
        expected = json.loads(packet_bytes)
        if expected['batch_id'] != batch or [p['id'] for p in expected['problems']] != assigned['ids']:
            raise ValueError('assignment identity mismatch')
        receipt['assignment_manifest_sha256'] = manifest_hash
        receipt['assignment_packet_sha256'] = sha(packet_bytes)
        files = checked_zip(retained / 'original.zip', wrapper=f'gamma-js-{batch}')
        if folder.is_symlink() or not folder.is_dir():
            raise ValueError('delivery folder must be a real directory')
        children = list(folder.iterdir())
        if any(p.is_symlink() or not p.is_file() for p in children):
            raise ValueError('nonregular member in downloaded folder')
        if {p.name for p in children} != set(files):
            raise ValueError('downloaded folder and ZIP contain different file sets')
        if any(p.stat().st_size > MAX_FILE or p.read_bytes() != files[p.name] for p in children):
            raise ValueError('downloaded folder differs from original ZIP')
        receipt['rows'] = verify_files(files, expected)
        extracted = retained / 'extracted'
        extracted.mkdir()
        for name, content in files.items():
            (extracted / name).write_bytes(content)
        receipt['files_sha256'] = {name: sha(content) for name, content in files.items()}
        target = lane / 'runs' / 'js-corpus-wave-002' / batch / f'delivery-{digest[:16]}'
        target.mkdir(parents=True, exist_ok=False)
        for row in receipt['rows']:
            number = row['id']
            for name in (f'{number:04d}.js', f'{number:04d}-semantics.json'):
                shutil.copyfile(extracted / name, target / name)
            row['source'] = str((target / f'{number:04d}.js').relative_to(lane))
            row['semantics'] = str((target / f'{number:04d}-semantics.json').relative_to(lane))
        receipt['status'] = 'imported-unqualified'
        receipt['target'] = str(target.relative_to(lane))
    except Exception as error:
        receipt['status'] = 'rejected'
        receipt['error'] = f'{type(error).__name__}: {error}'
    write_json(retained / 'receipt.json', receipt)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch', required=True)
    parser.add_argument('--archive', required=True, type=Path)
    parser.add_argument('--folder', required=True, type=Path)
    parser.add_argument('--authority', required=True, type=Path)
    parser.add_argument('--lane', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    result = import_delivery(args.archive, args.folder, args.authority, args.lane, args.batch)
    print(json.dumps(result, indent=2))
    if result['status'] == 'rejected':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
