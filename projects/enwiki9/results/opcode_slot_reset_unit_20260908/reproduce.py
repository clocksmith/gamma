"""Retain one synthetic ten-phase execution of the reset adapter."""
import json
import os
from pathlib import Path
import resource
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import opcode_slot_reset_gate_v1 as adapter
import opcode_field_compact_observe_v1 as old
os.sched_setaffinity(0,{3})
resource.setrlimit(resource.RLIMIT_AS,(2147483648,)*2)
resource.setrlimit(resource.RLIMIT_CPU,(240,)*2)
resource.setrlimit(resource.RLIMIT_FSIZE,(67108864,)*2)
out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=False)
raw=(b'<text xml:space="preserve">==References==\n</text><title>Next</title>')*3
inp=out/'input.raw';inp.write_bytes(raw)
arc,audit=old.execute(old.load(ROOT/'programs/opcode_field_compact_v1/program.py'),'encode',raw)
(out/'parent.arc').write_bytes(arc);(out/'parent.audit.json').write_text(json.dumps(audit))
plan=dict(input=dict(path=str(inp)),parent_archive=dict(path=str(out/'parent.arc')),
          parent_audit=dict(path=str(out/'parent.audit.json')))
gate=adapter.configure()
receipt=gate.run_comparison(out,plan,ROOT/'programs/opcode_slot_reset_v1',out/'phases.jsonl',
    dict(phase_cpu_seconds=10,phase_wall_seconds=15,phase_address_bytes=536870912))
gate.phase.write_json(out/'receipt.json',receipt)
print(json.dumps(dict(correctness_pass=receipt['correctness_pass'],
    bytes={k:v['archive_bytes'] for k,v in receipt['arms'].items()})))
