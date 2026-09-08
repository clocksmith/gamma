"""Retain the unchanged-parent synthetic calibration comparison."""
import json
import os
from pathlib import Path
import resource
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import opcode_calibration_gate_v1 as runner
import opcode_field_compact_observe_v1 as old
os.sched_setaffinity(0,{3})
resource.setrlimit(resource.RLIMIT_AS,(2147483648,)*2)
resource.setrlimit(resource.RLIMIT_CPU,(240,)*2)
resource.setrlimit(resource.RLIMIT_FSIZE,(67108864,)*2)
out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=False)
codec=ROOT/'programs/opcode_calibration_cost_v1'
raw=(b'<text xml:space="preserve">Oak. Oak. Oak.</text>\n')*6
(out/'input.raw').write_bytes(raw)
arc,audit=old.execute(old.load(codec/'program.py'),'encode',raw)
(out/'parent.arc').write_bytes(arc);(out/'parent.audit.json').write_text(json.dumps(audit))
plan=dict(input=dict(path=str(out/'input.raw')),parent_archive=dict(path=str(out/'parent.arc')),
          parent_audit=dict(path=str(out/'parent.audit.json')))
r=runner.run_comparison(out,plan,codec,out/'markers.jsonl',
    dict(phase_address_bytes=536870912,phase_cpu_seconds=10,phase_wall_seconds=15))
runner.gate.phase.write_json(out/'receipt.json',r)
print(json.dumps({k:r[k] for k in ('correctness_pass','archive_bytes','archive_saving_bytes','literal_sse_excess_bits')}))
