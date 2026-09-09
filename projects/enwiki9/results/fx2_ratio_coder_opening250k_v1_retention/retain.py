"""Retain only a closed opening gate; verify every reconstructed trace chunk."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / 'results/fx2_ratio_coder_opening250k_q0_v1'
OUT = Path(__file__).resolve().parent / 'retained'
JOB_ID = '20260909T073614Z_92f9e13b9e'
CHUNK = 64 * 1024 * 1024


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(1024 * 1024):
            h.update(block)
    return h.hexdigest()


def binding(path):
    return dict(path=str(path.relative_to(ROOT)), bytes=path.stat().st_size,
                sha256=digest(path))


def write(path, value):
    with path.open('x') as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True) + '\n')


def main():
    if sorted(os.sched_getaffinity(0)) != [3]:
        raise ValueError('retention requires assigned CPU3')
    jobs = list((ROOT / 'operations/adaptive/completed').glob('*' + JOB_ID + '*.json'))
    if len(jobs) != 1:
        raise ValueError('unique completed job required')
    job = json.loads(jobs[0].read_text())
    if not job['execution_resources']['cleanup_complete']:
        raise ValueError('native resource closure required')
    guard_path = ROOT / job['execution_resources']['guard_path']
    guard = json.loads(guard_path.read_text())
    if guard['status'] != 'complete' or guard['returncode'] != 0:
        raise ValueError('complete guard required')
    stage = json.loads((RUN / 'stage-decision.json').read_text())
    if stage['status'] != 'passed' or not stage['correctness_pass']:
        raise ValueError('closed correctness comparison required')
    manifest = json.loads((RUN / 'artifacts.json').read_text())
    OUT.mkdir(exist_ok=False)
    for row in manifest['files']:
        if binding(ROOT / row['path']) != row:
            raise ValueError('artifact changed: ' + row['path'])
    unique = {}
    traces = []
    for row in manifest['files']:
        source = ROOT / row['path']
        if source.suffix not in ('.ratio', '.coder'):
            continue
        key = row['sha256']
        if key not in unique:
            chunks = []
            total = hashlib.sha256()
            offset = 0
            with source.open('rb') as stream:
                while raw := stream.read(CHUNK):
                    path = OUT / (key + '.' + str(len(chunks)).zfill(3) + '.gz')
                    with path.open('xb') as encoded:
                        with gzip.GzipFile(filename='', mode='wb', fileobj=encoded,
                                           compresslevel=1, mtime=0) as zipper:
                            zipper.write(raw)
                    restored = gzip.decompress(path.read_bytes())
                    if restored != raw:
                        raise ValueError('chunk inverse failed')
                    total.update(restored)
                    chunks.append(dict(offset=offset, raw_bytes=len(raw),
                                       raw_sha256=hashlib.sha256(raw).hexdigest(),
                                       gzip=binding(path)))
                    offset += len(raw)
                    print(json.dumps(dict(trace=key, retained_bytes=offset)), flush=True)
            if total.hexdigest() != key or offset != row['bytes']:
                raise ValueError('whole trace reconstruction differs')
            unique[key] = chunks
        traces.append(dict(raw=row, chunks=unique[key], decompressed_hash_verified=True))
    members = [ROOT / row['path'] for row in manifest['files']
               if Path(row['path']).suffix not in ('.ratio', '.coder')]
    members.append(RUN / 'artifacts.json')
    bundle = OUT / 'closed-artifacts.zip'
    with zipfile.ZipFile(bundle, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=1) as archive:
        for path in members:
            info = zipfile.ZipInfo(str(path.relative_to(RUN)), date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o100755 if os.access(path, os.X_OK) else 0o100644) << 16
            archive.writestr(info, path.read_bytes())
    with zipfile.ZipFile(bundle) as archive:
        for path in members:
            if hashlib.sha256(archive.read(str(path.relative_to(RUN)))).hexdigest() != digest(path):
                raise ValueError('bundle inverse failed')
    receipt = dict(schema='gamma.enwiki9.native-trace-retention.v1',
                   job=binding(jobs[0]), guard=binding(guard_path),
                   artifact_files_rehashed=len(manifest['files']), raw_traces=traces,
                   unique_trace_count=len(unique), chunk_raw_limit_bytes=CHUNK,
                   reconstruction='For each raw trace, concatenate gzip-decoded chunks in listed offset order and verify its whole SHA256.',
                   closed_artifacts_zip=binding(bundle), bundle_members=len(members),
                   bundle_members_reconstructed_exactly=True, raw_files_preserved=True,
                   objective_credit_bytes=0)
    write(OUT.parent / 'receipt.json', receipt)
    print(json.dumps(dict(complete=True, unique_traces=len(unique), bundle=binding(bundle))))


if __name__ == '__main__':
    main()
