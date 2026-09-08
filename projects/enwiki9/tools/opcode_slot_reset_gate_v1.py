#!/usr/bin/env python3
"""Bind the existing ten-phase runner to the independently sealed reset experiment."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import opcode_wiki_slot_gate_v1 as runner


def configure():
    runner.CID='opcode_slot_reset_v1'
    runner.SELF='tools/opcode_slot_reset_gate_v1.py'
    runner.CLI='tools/opcode_slot_reset_observe_v1.py'
    return runner


if __name__=='__main__':raise SystemExit(configure().main())
