import copy
import unittest
import importlib.util
from pathlib import Path
spec = importlib.util.spec_from_file_location('stack_report_tests', Path(__file__).with_name('report.py'))
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)


def arm(name, policy, actions):
    rows = {str(i): {'encodable': True, 'actions': actions, 'selections': actions-1} for i in range(100)}
    d = {'covered': 100, 'qualified': 100,
         'actions': {'total': actions*100, 'median': actions, 'p90': actions},
         'single_character_fraction': .4, 'single_character_codes': 100,
         'package_bytes': 1000}
    return {'arm': name, 'policy': policy, 'entries': 256, 'illegal_entry_sha256': [],
            'fit': {'covered': 300, 'qualified': 300}, 'validation': d, 'per_problem': rows}


class PromotionTests(unittest.TestCase):
    def build(self, candidate_actions=80):
        rows = []
        for policy in report.POLICIES:
            for name in ('R', 'seed13', 'best24', *report.CANDIDATES):
                actions = {'R': 100, 'seed13': 90, 'best24': 80, 'N': 90}.get(name, candidate_actions)
                rows.append(arm(name, policy, actions))
        return {'arms': rows}, {'partition': {'dev_val': list(range(100))}}

    def test_retains_current_best_when_no_strict_gain(self):
        raw, contract = self.build()
        result = report.build(raw, contract)
        self.assertIsNone(result['selected_successor'])
        self.assertEqual(result['retained_default'], {'arm': 'best24', 'policy': 'canonical'})

    def test_policy_comparisons_do_not_mix(self):
        raw, contract = self.build(79)
        # Improved primary candidate must compare against improved PRIMARY24,
        # not the weaker canonical24 reference.
        best = next(a for a in raw['arms'] if a['arm']=='best24' and a['policy']=='shortest_min_char')
        best['validation']['single_character_fraction'] = .3
        result = report.build(raw, contract)
        self.assertIsNone(result['selected_successor'])
        self.assertIsNotNone(result['selected_by_policy']['canonical'])

    def test_wrong_source_qualification_blocks(self):
        raw, contract = self.build(79)
        for a in raw['arms']:
            if a['arm'] in report.CANDIDATES:
                a['fit']['qualified'] = 299
        result = report.build(raw, contract)
        self.assertIsNone(result['selected_successor'])

    def test_weighted_output_must_beat_own_control(self):
        raw, contract = self.build(79)
        result = report.build(raw, contract)
        for a in result['arms']:
            if a['arm'] in ('D01', 'D11'):
                self.assertFalse(a['successor'])
                self.assertFalse(a['incremental_checks'][a['arm'][:2]+'0']['actions'])



class IndependentReplayTests(unittest.TestCase):
    """Toy source packets catch corrupt metadata and false qualification claims."""
    def fixture(self,folder,uncovered=False):
        import engine as e
        import run
        sources={'1':'function solve(a){return a+1;}', '2':'function solve(a){return a+2;}'}
        vocab=['ZZ'] if uncovered else e.slots.ALPHABET+['function solve(','){return ']
        c={'partition':{'dev_fit':[1],'dev_val':[2]},'decoder_dependency_bytes':13010}
        banned=e.base.sel.forbidden_strings(sources)
        arm=run.measure('toy',sources,vocab,banned,folder,c)[0]
        known={}
        for pid,row in arm['per_problem'].items():
            q={'passed':True,'reused':True,'receipt_source':'toy_sealed_source'}
            known[pid,row['source_sha256']]=q
            arm.setdefault('qualification',{})[pid]=q
            row['qualified_source']=True
        for split,group in (('fit','dev_fit'),('validation','dev_val')):
            arm[split]['qualified']=sum(arm['per_problem'][str(pid)]['encodable'] for pid in c['partition'][group])
        base=folder/'artifacts/toy'
        args=(arm,sources,vocab,(base/'dictionary.bin').read_bytes(),base/'canonical',banned,c,e,known,{})
        return args

    def test_corrupt_per_program_and_aggregate_costs_rejected(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            args=self.fixture(Path(tmp))
            report.replay_arm(*args)
            arm=args[0]
            arm['per_problem']['1']['single_characters']-=1
            with self.assertRaises(AssertionError):report.replay_arm(*args)
            arm['per_problem']['1']['single_characters']+=1
            arm['validation']['actions']['total']-=1
            with self.assertRaises(AssertionError):report.replay_arm(*args)

    def test_rejected_fresh_receipt_cannot_be_published_as_pass(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            args=list(self.fixture(Path(tmp)));arm=args[0]
            row=arm['per_problem']['2'];key=('2',row['source_sha256'])
            del args[8][key]
            args[9][f'2:{key[1]}']={'passed':False,'checks_passed':0,'cases':1,'reused':False}
            with self.assertRaises(AssertionError):report.replay_arm(*args)
            arm['qualification']['2']=args[9][f'2:{key[1]}']
            row['qualified_source']=False;arm['validation']['qualified']=0
            report.replay_arm(*args)

    def test_illegal_comparator_cannot_qualify_a_successor(self):
        candidate=arm('candidate','canonical',70)
        comparator=arm('baseline','canonical',90)
        comparator['illegal_entry_sha256']=['synthetic_illegal_entry']
        self.assertFalse(report.checks(candidate,comparator,list(range(100)))['legal_dictionary'])

    def test_all_unencodable_is_retained_and_printable(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            args=self.fixture(Path(tmp),True);arm=args[0]
            report.replay_arm(*args)
            arm['successor']=False
            line=report.display_cost_row(arm)
            self.assertIn('unavailable',line)
            self.assertEqual(arm['validation']['covered'],0)
            self.assertFalse(all(report.checks(arm,arm,[2]).values()))

    def test_full_sealed_toy_artifacts_replay_without_corpus(self):
        import tempfile
        from unittest import mock
        import engine as e
        import run
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);fit={'1':'function solve(a){return a+1;}'};val={'2':'function solve(a){return a+2;}'}
            sources={**fit,**val};vocab=e.slots.ALPHABET+['function solve(','){return ']
            fit_banned=e.base.sel.forbidden_strings(fit);all_banned=e.base.sel.forbidden_strings(sources)
            c={'partition':{'dev_fit':[1],'dev_val':[2]},'decoder_dependency_bytes':13010,
               'code_hashes':{rel:e.analyze.sha((e.LIT/rel).read_bytes()) for rel in ('literals.py','pass2/working/bitpack.py')},
               'references':{'R':'refR','seed13':'ref13','best24':'ref24'},'private_files':{}}
            summaries=[]
            for name in report.CANDIDATES:
                root=folder/'fit'/name;root.mkdir(parents=True)
                e.analyze.write(root/'dictionary.json',vocab);e.analyze.write(root/'fit-sources.json',fit)
                e.analyze.write(root/'fit-banned.json',sorted(fit_banned))
                if name in e.SOURCE_ARMS:e.analyze.write(root/'fit-variants.json',e.normalized({pid:[text] for pid,text in fit.items()}))
                digest=e.seal(root,{})
                summaries.append({'arm':name,'fit_seal_sha256':digest})
            for name in e.SOURCE_ARMS:
                root=folder/'fit'/name
                e.analyze.write(root/'validation-sources.json',val)
                e.analyze.write(root/'validation-variants.json',e.normalized({pid:[text] for pid,text in val.items()}))
                e.analyze.write(root/'all-banned.json',sorted(all_banned))
                seal={'qualification_started':False,'source_sha256':e.digest(val),
                      'dictionary_sha256':e.analyze.sha((root/'dictionary.json').read_bytes()),
                      'files':{file:e.analyze.sha((root/file).read_bytes()) for file in ('validation-sources.json','validation-variants.json','all-banned.json')}}
                e.analyze.write(root/'validation-seal.json',seal)
            e.analyze.write(folder/'all-fit-sealed.json',{'validation_loaded':False,'arms':summaries,'repairs':[]})
            e.analyze.write(folder/'all-validation-sealed.json',{'qualification_started':False,'arms':[]})
            e.analyze.write(folder/'status.json',{'complete':True});e.analyze.write(folder/'supervisor-receipt.json',{'complete':True})
            known={};arms=[]
            for name in ('R','seed13','best24',*report.CANDIDATES):
                group=run.measure(name,sources,vocab,all_banned,folder,c)
                if name in c['references']:
                    base=folder/'artifacts'/name
                    source_name='seed13' if name=='best24' else name
                    c['private_files'][c['references'][source_name]+'/sources.json']=e.analyze.sha((base/'sources.json').read_bytes())
                    c['private_files'][c['references'][name]+'/dictionary.json']=e.analyze.sha((base/'dictionary.json').read_bytes())
                for a in group:
                    a['qualification']={}
                    for pid,row in a['per_problem'].items():
                        q={'passed':True,'reused':True,'receipt_source':'toy'}
                        known[pid,row['source_sha256']]=q;a['qualification'][pid]=q;row['qualified_source']=True
                    a['fit']['qualified']=a['validation']['qualified']=1
                arms+=group
            raw={'arms':arms,'fit_summaries':summaries,'repair_summaries':[],'decoded_packets':44,
                 'fresh_qualification_summary':{'distinct_new_sources':0,'passed':0,'checks_passed':0,'checks':0,'failed_sources':0}}
            with mock.patch.object(report,'qualification_authority',return_value=(known,{},{})):
                report.verify_run_artifacts(folder,raw,c,e)
                (folder/'failure.json').write_text('{}')
                with self.assertRaises(AssertionError):report.verify_run_artifacts(folder,raw,c,e)


if __name__ == "__main__":
    unittest.main()
