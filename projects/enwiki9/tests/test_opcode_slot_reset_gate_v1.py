"""Exercise the existing runner with the reset adapter and unchanged failure guards."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
sys.path.insert(0,str(ROOT/'tests'))
import opcode_slot_reset_gate_v1 as adapter
import test_opcode_wiki_slot_gate_v1 as original


class ResetGateTests(original.GateTests):
    def setUp(self):
        self.saved=(original.gate.CID,original.gate.SELF,original.gate.CLI)
        adapter.configure()
        super().setUp()
        self.snapshot=ROOT/'programs/opcode_slot_reset_v1'
        self.raw=(b'<text xml:space="preserve">==References==\n'
                  b'</text><title>Next</title>')*3
        self.input.write_bytes(self.raw)
        archive,audit=original.old.execute(original.old.load(
            ROOT/'programs/opcode_field_compact_v1/program.py'),'encode',self.raw)
        self.arc.write_bytes(archive);self.audit.write_text(original.json.dumps(audit))

    def tearDown(self):
        try:super().tearDown()
        finally:original.gate.CID,original.gate.SELF,original.gate.CLI=self.saved


if __name__=='__main__':original.unittest.main(verbosity=2)
