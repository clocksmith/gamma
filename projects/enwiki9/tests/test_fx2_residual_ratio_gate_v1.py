import struct
from pathlib import Path
import tempfile
import unittest
from projects.enwiki9.tools import fx2_residual_ratio_fixture50051_q0_v1 as gate


class GateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
    def trace(self):
        chunks=[]
        for i,event in enumerate(b'IPOP'):
            state=struct.pack('<4sHcBQ',b'GRR1',205,b'D',i%2,i//2)+bytes(205*12)
            chunks.append(bytes([event])+struct.pack('<I',len(state))+state)
        return b''.join(chunks)
    def test_complete_native_state_framing(self):
        path=self.root/'trace';path.write_bytes(self.trace())
        self.assertEqual(gate.validate_ratio_trace(path,'D',2)['records'],4)
    def test_wrong_state_event_arm_position_and_truncation_rejected(self):
        raw=self.trace();path=self.root/'trace'
        for bad in (raw[:-1],b'P'+raw[1:],raw[:11]+b'S'+raw[12:],raw[:13]+b'\x01'+raw[14:]):
            path.write_bytes(bad)
            with self.assertRaises(ValueError):gate.validate_ratio_trace(path,'D',2)
    def test_exact_comparison_detects_first_changed_byte(self):
        a=self.root/'a';b=self.root/'b';a.write_bytes(b'abcd');b.write_bytes(b'abXd')
        with self.assertRaisesRegex(ValueError,'byte 2'):gate.equal_files(a,b)
        b.write_bytes(a.read_bytes());gate.equal_files(a,b)


if __name__=='__main__':unittest.main()
