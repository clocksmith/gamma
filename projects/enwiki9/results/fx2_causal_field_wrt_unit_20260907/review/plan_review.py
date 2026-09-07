#!/usr/bin/env python3
"""Read only frozen source and receipt metadata; never open corpus/trace payloads."""
import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path('/home/x/deco/gamma/projects/enwiki9')
OUT = Path(__file__).resolve().parent
PLAN = 'operations/provenance/fx2_causal_field_wrt_replay250k_q0_v1_plan.json'
EXPECTED_PLAN = '46da8bedfffac3c941d1d0220d4afe906c2ee113f52b4a27dcf6b5a5ef079f7c'

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

plan_raw = (ROOT / PLAN).read_bytes()
assert sha(plan_raw) == EXPECTED_PLAN
plan = json.loads(plan_raw)
references = []
for ref in plan['inputs']:
    raw = (ROOT / ref['path']).read_bytes()
    assert len(raw) == ref['bytes'] and sha(raw) == ref['sha256'], ref['path']
    references.append(dict(ref))
audit_path = 'operations/provenance/public_fx2_weight_native_transfer_terminal_20260905.json'
audit = json.loads((ROOT / audit_path).read_text())
opening = next(row for row in audit['population']['populations'] if row['name'] == 'opening')
trace = next(row for row in audit['coder_records'] if row['path'].endswith('/opening-P-encode.trace'))
assert opening['raw_bytes'] == 250000 and opening['modeled_bytes'] == 151210
assert opening['stored']['bytes'] == 151220 and opening['archive_bytes'] == 33429
assert trace['bytes'] == opening['modeled_bytes'] * 8 * 28 == 33871040
assert opening['first_block_header_hex'] == '070003d090'
assert opening['arms']['P']['archive']['sha256'] == '70325310e96b83b48677d76d53141e69ddb47519b4cdffd1c85f51fe2c444dbe'
assert trace['sha256'] == 'a5a0afbf0715a9c5371d5f097aaa1b478c1c6a2c030448c79b4ca70f1279c716'
result = {
    'schema': 'gamma.independent-field-wrt-plan-review.v1',
    'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'plan': {'path': PLAN, 'sha256': EXPECTED_PLAN},
    'references_checked': references,
    'read_scope': 'source and terminal receipt metadata only; no raw, stored, archive or trace payload files opened',
    'opening': {
        'raw_bytes': 250000, 'stored_header_bytes': 10, 'modeled_bytes': 151210,
        'native_trace_record_bytes': 28, 'native_trace_records': 1209680,
        'native_trace_bytes': 33871040,
        'native_trace_words': ['float_bits', 'q16', 'pre_low', 'pre_high', 'post_low', 'post_high', 'bit'],
        'archive_prefix_components': {'GFV1': 4, 'literal_type_and_raw_length': 5,
                                      'modeled_length_and_trained_flag': 5, 'vocabulary_bitmap': 32},
        'archive_prefix_bytes': 46, 'arithmetic_payload_bytes': 33383, 'complete_archive_bytes': 33429,
        'trace_reference': trace, 'archive_reference': opening['arms']['P']['archive'],
    },
    'obligations': [
        'P and K reproduce the exact complete parent archive including the 46-byte prefix.',
        'Native Q16 values are used directly without float requantization.',
        'Native arithmetic byte renormalization and final flush are reproduced exactly.',
        'Q16-only decoder input omits all native trace truth and interval columns.',
        'Decoder reconstruction plus canonical re-encoding validates native zero extension.',
        'Q16 dependency remains external diagnostic input and earns no standalone/package credit.',
    ],
    'command': ['taskset', '-c', '3', 'python3', '-B', str(Path(__file__))],
}
target = OUT / 'plan-review.json'
with target.open('x') as stream:
    json.dump(result, stream, sort_keys=True, indent=2)
    stream.write('\n')
print(json.dumps({'status': 'passed', 'artifact': str(target), 'sha256': sha(target.read_bytes())}, sort_keys=True))
