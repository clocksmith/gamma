#!/usr/bin/env python3
"""Materialize unchanged codec files and the separately frozen audit retry plan."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CID='opcode_previous_word_confirmation1m_q0_v4'
PLAN=ROOT/'operations/provenance/opcode_previous_word_confirmation1m_v4_inputs.json'
def main():
    plan=json.loads(PLAN.read_text())
    for source,target in zip(plan['materialization'],plan['package_files']):
        data=(ROOT/source['path']).read_bytes()
        assert hashlib.sha256(data).hexdigest()==source['sha256']==target['sha256']
        path=ROOT/target['path'];path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(data)
    (ROOT/'programs'/CID/'gate-plan.json').write_bytes(PLAN.read_bytes())
if __name__=='__main__':main()
