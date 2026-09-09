"""Retain this closed experiment using the existing native-trace-retention format."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import zipfile

os.sched_setaffinity(0, {3})
resource.setrlimit(resource.RLIMIT_AS, (512 << 20, 512 << 20))
resource.setrlimit(resource.RLIMIT_CPU, (240, 240))
resource.setrlimit(resource.RLIMIT_FSIZE, (100 << 20, 100 << 20))
signal.alarm(360)
ROOT = Path(__file__).resolve().parents[2]
os.chdir(ROOT)
BASE = Path('results/fx2_xml_word_opening250k_q0_v1')
OUT = Path('results/fx2_xml_word_opening250k_v1_retention')
DEST = OUT / 'retained'
DEST.mkdir(exist_ok=False)
LIMIT = 64 << 20


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def ref(path):
    return dict(path=str(path), bytes=Path(path).stat().st_size, sha256=digest(path))


manifest = json.loads((BASE / 'artifacts.json').read_text())
files = manifest['files']
assert not manifest['errors']
for item in files:
    assert ref(item['path']) == item, item['path']
traces = [x for x in files if Path(x['path']).suffix in ('.coder', '.xml')]
assert len(traces) == 21
objects = {}
rows = []
for item in traces:
    sha = item['sha256']
    if sha not in objects:
        chunks = []
        whole = hashlib.sha256()
        offset = 0
        with Path(item['path']).open('rb') as stream:
            while raw := stream.read(LIMIT):
                packed = gzip.compress(raw, compresslevel=6, mtime=0)
                name = DEST / f'{sha}.{len(chunks):03d}.gz'
                with name.open('xb') as output:
                    output.write(packed)
                restored = gzip.decompress(name.read_bytes())
                assert restored == raw
                whole.update(restored)
                chunks.append(dict(offset=offset, raw_bytes=len(raw),
                                   raw_sha256=hashlib.sha256(raw).hexdigest(), gzip=ref(name)))
                offset += len(raw)
                assert sum(p.stat().st_size for p in DEST.iterdir()) < 1 << 30
        assert whole.hexdigest() == sha and offset == item['bytes']
        objects[sha] = chunks
        print('retained', sha, offset, flush=True)
    rows.append(dict(raw=item, chunks=objects[sha], decompressed_hash_verified=True))
trace_paths = {x['path'] for x in traces}
small = [Path(x['path']) for x in files if x['path'] not in trace_paths]
small += [BASE / 'artifacts.json', BASE / 'stage-decision.json']
bundle = DEST / 'closed-artifacts.zip'
with zipfile.ZipFile(bundle, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
    for path in sorted(small):
        entry = zipfile.ZipInfo(str(path), date_time=(1980, 1, 1, 0, 0, 0))
        entry.compress_type = zipfile.ZIP_DEFLATED
        entry.external_attr = 0o100644 << 16
        archive.writestr(entry, path.read_bytes())
with zipfile.ZipFile(bundle) as archive:
    assert archive.namelist() == [str(x) for x in sorted(small)]
    for path in small:
        assert archive.read(str(path)) == path.read_bytes()
receipt = dict(schema='gamma.enwiki9.native-trace-retention.v1',
               artifact_manifest=ref(BASE / 'artifacts.json'),
               job=ref('operations/adaptive/completed/090_20260909T102756Z_82a65eed5d.json'),
               guard=ref('run_logs/adaptive/20260909T102756Z_82a65eed5d.resources/guard.json'),
               retention_source=ref(Path(__file__).resolve().relative_to(ROOT)),
               artifact_files_rehashed=len(files), raw_traces=rows,
               unique_trace_count=len(objects), chunk_raw_limit_bytes=LIMIT,
               closed_artifacts_zip=ref(bundle), bundle_members=len(small),
               bundle_members_reconstructed_exactly=True, raw_files_preserved=True,
               reconstruction='Extract ZIP project-relative members; concatenate each trace gzip chunk in offset order and verify whole SHA256.',
               bounds=dict(cpu=3, address_space_bytes=512 << 20, cpu_seconds=240,
                           wall_seconds=360, scratch_bytes=1 << 30),
               objective_credit_bytes=0)
with (OUT / 'receipt.json').open('x') as output:
    json.dump(receipt, output, indent=2, sort_keys=True)
    output.write('\n')
print('complete', len(objects), len(files), flush=True)
