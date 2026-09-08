"""Reuse the published fixed ZIP diagnostic for the unchanged field-history bundle."""
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
    'treatment': ('opcode_field_history250k_q0_v1', {
        'p': '2d29f154a9df186caa7b547fa304820b6ceb6d675aef59005d7a1319febf3c64',
        'program.py': 'b96d641dc5a84dc9130932cca52d62b7fcefa54c2a0fce39027cb95bc1eee2ae'})}
module.main()
out = Path(sys.argv[1]).resolve()
receipt = json.loads((out / 'receipt.json').read_text())
counts = {r['name']: r['source_zip']['bytes'] for r in receipt['rows']}
wrapper = dict(schema='gamma.enwiki9.opcode-field-history-source-cost.v1',
    caller=module.record(Path(__file__).resolve()), receipt=module.record(out / 'receipt.json'),
    source_zip_bytes=counts, added_source_zip_bytes=counts['treatment']-counts['parent'],
    conditional_shared_program_multiplicity=2,
    conditional_added_counted_source_bytes=2*(counts['treatment']-counts['parent']),
    corpus_executed=False, complete_package_bytes=None, objective_credit_bytes=0,
    bounds=dict(cpu=3, threads=1, address_space_bytes=2147483648, cpu_seconds=90,
                outer_wall_seconds=120, file_bytes=67108864),
    note='One unchanged source-ZIP policy, exact member hashes and six synthetic relocated phases. '
         'Runtime, options, licenses and accepted multiplicities remain unresolved. '
         'No corpus result is inspected or inferred by this diagnostic.')
with (out / 'cost.json').open('x') as stream:
    json.dump(wrapper, stream, sort_keys=True, indent=2)
    stream.write('\n')
