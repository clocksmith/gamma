"""Changing the active objective must not rewrite historical proof identities."""
import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import research_contracts as contracts


class ObjectiveMigrationTests(unittest.TestCase):
    def test_active_complete_budget(self):
        binding = contracts.objective_binding()
        self.assertEqual(binding['objectiveId'], 'gamma-enwiki9-hutter-90m-v3')
        self.assertEqual(binding['targetScoreBytes'], 90000000)
        self.assertEqual(binding['corpusBytes'], 1000000000)
        self.assertEqual(binding['targetScoreBytes']*8, 720000000)
        contracts.validate_artifact(contracts.OBJECTIVE_PATH)

    def test_historical_digests_preserved(self):
        cases = [('v1',105000000,'ce4c435c0f398caf65a09050c8518d9c5ea63239f9156048ea2aaaf9b8ffa7e8'),
                 ('v2',99000000,'16badfa6c1a53b47bcc12b089fdd9c21f7405ea56a84344d60c28d2252da8288')]
        for version,target,digest in cases:
            binding = contracts.objective_binding(objective_path=f'contracts/research/{version}/objective-contract.json')
            self.assertEqual(binding['targetScoreBytes'],target)
            self.assertEqual(binding['objectiveDigest'],'sha256:'+digest)
            contracts._validate_objective_binding(binding,'historical')

    def test_relabelled_old_binding_rejected(self):
        old = contracts.objective_binding(objective_path='contracts/research/v2/objective-contract.json')
        changed = copy.deepcopy(old)
        changed['targetScoreBytes']=90000000
        with self.assertRaises(ValueError):
            contracts._validate_objective_binding(changed,'changed')

    def test_only_target_and_migration_change_obligations(self):
        old = contracts.validate_objective(objective_path='contracts/research/v2/objective-contract.json')
        new = contracts.validate_objective()
        for name in ('corpus','correctness','resources','distribution','evidence','epistemicPolicy','promotionLadders'):
            self.assertEqual(old[name],new[name],name)
        self.assertEqual(old['score']['formula'],new['score']['formula'])
        self.assertEqual(new['migration']['previousObjectiveDigest'],
                         contracts.objective_binding(objective_path='contracts/research/v2/objective-contract.json')['objectiveDigest'])


if __name__=='__main__':
    unittest.main(verbosity=2)
