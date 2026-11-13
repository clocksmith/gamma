import tempfile
import unittest
from pathlib import Path
from projects.distillation.wgsl.channel_gain.decision import paired_sign, gap_closure, select_public_sample, freeze_confirmation, smoke_eta

class DecisionTest(unittest.TestCase):
    def test_sign_and_underpower(self):
        self.assertEqual(paired_sign(dict.fromkeys(range(4), True), dict.fromkeys(range(4), False))["status"], "underpowered")
        result = paired_sign(dict.fromkeys(range(5), True), dict.fromkeys(range(5), False))
        self.assertEqual(result["pOneSided"], 1/32)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(paired_sign(dict.fromkeys(range(5), False), dict.fromkeys(range(5), True))["status"], "fail")
        with self.assertRaises(ValueError): paired_sign({"a": True}, {"b": False})
    def test_gap(self):
        self.assertEqual(gap_closure(5, 2, 6)["status"], "pass")
        self.assertEqual(gap_closure(5, 3, 6)["status"], "uninformative")
    def test_public_selection(self):
        samples=[{"sampleId": x,"publicChecks":[{"id":"compile","passed":True,"visibility":"public"}]} for x in ["first","second"]]
        self.assertEqual(select_public_sample(samples), "first")
        samples[1]["publicChecks"][0]["visibility"]="confirmation"
        with self.assertRaises(ValueError): select_public_sample(samples)
    def test_lock_is_write_once(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"lock.json"; args=dict(protocol_hash="a"*64,task_hash="b"*64,oracle_hash="c"*64,selection_hash="d"*64,candidate="gain-positive",submissions={"task/base":"e"*64})
            freeze_confirmation(p,**args)
            with self.assertRaises(FileExistsError): freeze_confirmation(p,**args)
    def test_eta_needs_measurements(self):
        with self.assertRaises(ValueError): smoke_eta([], 8)
        self.assertEqual(smoke_eta([1000,3000],4)["meanSeconds"],8)

if __name__ == '__main__': unittest.main()
