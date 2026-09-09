"""One fixed source-ZIP diagnostic alongside the independent corpus job."""
import importlib.util
import json
import os
from pathlib import Path
import resource
import sys

ROOT = Path(__file__).resolve().parents[2]
os.sched_setaffinity(0, {3})
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
resource.setrlimit(resource.RLIMIT_AS, (2147483648,) * 2)
resource.setrlimit(resource.RLIMIT_CPU, (90,) * 2)
resource.setrlimit(resource.RLIMIT_FSIZE, (67108864,) * 2)
path = ROOT / 'results/opcode_field_source_zip_diagnostic_20260908/reproduce.py'
spec = importlib.util.spec_from_file_location('existing_source_zip_diagnostic', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.SOURCES = {
    'parent': ('opcode_field_compact_v1', {
        'p': '7d331ba82c635af8afe6517bf5f4471b41dcf7854c6ec01cb5564078d9bb56a8',
        'program.py': '7361c8aa3695ec9d1556be02de66a1f0781414e78b44827511fb08bf8c8c05eb'}),
    'treatment': ('opcode_event_parse250k_q0_v1', {
        'p': '7d331ba82c635af8afe6517bf5f4471b41dcf7854c6ec01cb5564078d9bb56a8',
        'v': 'd9c4d28792936916715d37b1ace4572c0cdc2cc106498077418a3f32b66de48b',
        'program.py': '12ed0a23ee98326da0d0c174d726cdbc6543c3cf8921d326cb967d0a99f55c1b'})}
module.main()
out = Path(sys.argv[1]).resolve()
receipt = json.loads((out / 'receipt.json').read_text())
counts = {r['name']: r['source_zip']['bytes'] for r in receipt['rows']}
result = dict(schema='gamma.enwiki9.opcode-event-parse-source-cost.v1',
    caller=module.record(Path(__file__).resolve()), receipt=module.record(out / 'receipt.json'),
    source_zip_bytes=counts, added_source_zip_bytes=counts['treatment']-counts['parent'],
    corpus_executed=False, complete_package_bytes=None, objective_credit_bytes=0,
    bounds=dict(cpu=3, threads=1, address_space_bytes=2147483648, cpu_seconds=90,
                outer_wall_seconds=120, file_bytes=67108864),
    note='Fixed ZIP policy, authenticated members, independent relocated synthetic inverse and repeat. '
         'Source-component cost only. Runtime, licenses, options and official multiplicities remain unresolved. '
         'No inspection of the active corpus job or inference of its result.')
with (out / 'cost.json').open('x') as stream:
    json.dump(result, stream, sort_keys=True, indent=2)
    stream.write('\n')
