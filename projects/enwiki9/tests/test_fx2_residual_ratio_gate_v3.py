import unittest
from projects.enwiki9.tools import fx2_residual_ratio_fixture50051_q0_v3 as gate


class ActivationTests(unittest.TestCase):
    def test_native_progress_prefix_and_line_endings(self):
        for arm in 'PKDS':
            for prefix in (b'',b'\rpreprocessing...',b'progress\r'):
                for end in (b'\n',b'\r\n'):
                    gate.validate_activation(prefix+b'Gamma ratio selected='+arm.encode()+end,arm)

    def test_missing_wrong_duplicate_or_malformed_marker(self):
        for message in (b'',b'Gamma ratio selected=P\n',b'Gamma ratio selected=DD\n',
                        b'Gamma ratio selected=D',b'Gamma ratio selected=D\nGamma ratio selected=D\n',
                        b'Gamma ratio selected=D\nGamma ratio selected=broken'):
            with self.assertRaises(ValueError):gate.validate_activation(message,'D')


if __name__=='__main__':unittest.main()
