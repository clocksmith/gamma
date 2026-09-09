"""Matched delivery-only measurement; never execute or alter measured codec source."""
import hashlib
import io
import json
import resource
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent


def ref(path):
    data = path.read_bytes()
    return dict(path=str(path.relative_to(ROOT)), bytes=len(data),
                sha256=hashlib.sha256(data).hexdigest())


def packed(files):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED,
                             compresslevel=9)
    return stream.getvalue()


start = time.monotonic()
rows = {}
for arm, candidate, names in [
    ('P', 'opcode_field_compact_v1', ('p', 'program.py')),
    ('D', 'opcode_previous_word250k_q0_v1', ('p', 'v', 'program.py')),
]:
    paths = [ROOT / 'programs' / candidate / name for name in names]
    files = {p.name: p.read_bytes() for p in paths}
    data = packed(files)
    assert packed(files) == data
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        assert archive.testzip() is None
        assert {name: archive.read(name) for name in archive.namelist()} == files
    path = OUT / (arm + '.zip')
    with path.open('xb') as stream:
        stream.write(data)
    rows[arm] = dict(inputs=[ref(p) for p in paths], archive=ref(path),
                     repeat_equal=True, extracted_files_equal=True)
increment = rows['D']['archive']['bytes'] - rows['P']['archive']['bytes']
report = dict(schema='gamma.enwiki9.source-delivery-measurement.v1',
              scope='Unchanged local source bundles only; Python, libraries, invocation and official multiplicities unresolved.',
              policy='ZIP Deflate level9; sorted bare member names; fixed1980 timestamp and mode100644; no tuning.',
              codec_execution=False, rows=rows, source_zip_increment_bytes=increment,
              development_archive_saving_bytes=147,
              archive_plus_source_zip_saving_bytes=147-increment,
              complete_package_bytes=None, full_corpus_score_bytes=None,
              objective_credit_bytes=0, elapsed_seconds=time.monotonic()-start,
              peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
print(json.dumps(report, indent=2, sort_keys=True))
