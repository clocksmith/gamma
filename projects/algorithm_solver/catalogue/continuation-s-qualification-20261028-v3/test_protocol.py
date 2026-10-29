"""S20 v3 rerun controller: source-free binding/selection/fail-closed controls.

The sandbox is mocked and no candidate source is opened or executed.
The dispatch control uses an inert fixture body.
"""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch
import protocol as p

HERE=Path(__file__).resolve().parent
V1_OBSERVER=HERE.parent/'continuation-s-observers-20261028-v1'


def load_v2_controller():
    spec=importlib.util.spec_from_file_location('s20_v2_controller_for_comparison',HERE.parent/'continuation-s-qualification-20261028-v2/protocol.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


class ObserverBinding(unittest.TestCase):
    def test_profile_is_observer_v2_with_v1_lineage(self):
        self.assertEqual(p.OBSERVER.name,'continuation-s-observers-20261028-v2')
        self.assertEqual(p.sha((p.OBSERVER/'native-bindings.json').read_bytes()),p.PROFILE_SHA)
        self.assertEqual(p.PROFILE['previous_profile_sha256'],p.PRIOR_PROFILE_SHA)
        self.assertEqual(p.sha((V1_OBSERVER/'native-bindings.json').read_bytes()),p.PRIOR_PROFILE_SHA)
        self.assertEqual(p.PROFILE['route'],'official-s-v1')

    def test_only_javascript_observer_bytes_change(self):
        v1={r['path']:r['sha256'] for r in json.loads((V1_OBSERVER/'native-bindings.json').read_text())['files']}
        for name in ('harness.py','native_graphs.py','host_check.py','plan.py','prospective-plan.json'):
            self.assertEqual(p.PROFILE['files'][name],v1[name],name)
        for name in ('harness.cjs','native_graphs.cjs'):
            self.assertNotEqual(p.PROFILE['files'][name],v1[name],name)

    def test_argv_limits_plan_checker_and_supplement_unchanged_from_v2_controller(self):
        v2=load_v2_controller()
        self.assertEqual(p.ARGV,v2.ARGV);self.assertEqual(p.asdict(p.E.LIMITS),p.asdict(v2.E.LIMITS))
        self.assertEqual(p.E.LIMITS.cpu_seconds,3);self.assertEqual(p.E.LIMITS.wall_seconds,8);self.assertEqual(p.E.LIMITS.memory_bytes,1024**3)
        self.assertEqual((p.PLAN_SHA,p.MANIFEST_SHA,p.SCOPE_NOTE_SHA,p.SAFETY_REVIEW_TEXT,p.FLAGS),(v2.PLAN_SHA,v2.MANIFEST_SHA,v2.SCOPE_NOTE_SHA,v2.SAFETY_REVIEW_TEXT,v2.FLAGS))
        self.assertEqual(p.sha(Path(p.CHECK.__file__).read_bytes()),p.sha(Path(v2.CHECK.__file__).read_bytes()))
        self.assertEqual((HERE/'required-domain-supplement.json').read_bytes(),(HERE.parent/'continuation-s-qualification-20261028-v2/required-domain-supplement.json').read_bytes())
        self.assertEqual((p.PRIOR_SOURCE_REVIEW_SHA,p.PRIOR_OBSERVER_REVIEW_SHA,p.PRIOR_PROFILE_SHA),(v2.SOURCE_REVIEW_SHA,v2.OBSERVER_REVIEW_SHA,v2.PROFILE_SHA))


class Selection(unittest.TestCase):
    def test_exact_rerun_selection_after_full_inventory(self):
        rows,_=p.metadata()
        self.assertEqual(tuple(rows),p.RERUN);self.assertEqual(p.RERUN,((222,'javascript'),))

    def test_missing_rerun_slot_rejected(self):
        with patch.object(p,'RERUN',p.RERUN+((999,'javascript'),)):
            with self.assertRaisesRegex(ValueError,'exact rerun selection'):p.metadata()


class ReviewsFailClosed(unittest.TestCase):
    def test_no_review_approves_nothing(self):
        rows,contract=p.metadata()
        result=p.reviews(SimpleNamespace(review=None),rows,contract)
        self.assertEqual(set(result),{'222:javascript'});self.assertFalse(result['222:javascript']['approved'])

    def test_unpinned_receipts_refused(self):
        self.assertIsNone(p.SOURCE_REVIEW_SHA);self.assertIsNone(p.OBSERVER_REVIEW_SHA)
        rows,contract=p.metadata()
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'review.json';path.write_text('{}')
            with self.assertRaisesRegex(ValueError,'not yet pinned'):p.reviews(SimpleNamespace(review=path),rows,contract)
            with self.assertRaisesRegex(ValueError,'not yet pinned'):p.observer_review(SimpleNamespace(observer_review=path))

    def test_v1_bound_review_cannot_approve_v2_binding(self):
        rows,contract=p.metadata();pins=p.binding(222,'javascript',rows[222,'javascript'],contract)
        self.assertEqual(pins['observer_sha256'],p.PROFILE['files']['harness.cjs'])
        v1={r['path']:r['sha256'] for r in json.loads((V1_OBSERVER/'native-bindings.json').read_text())['files']}
        record={**pins,'observer_profile_sha256':p.PRIOR_PROFILE_SHA,'observer_sha256':v1['harness.cjs'],'native_graphs_sha256':v1['native_graphs.cjs'],
                'reviewer':'synthetic','source_safety':p.SAFETY_REVIEW_TEXT,**{flag:True for flag in p.FLAGS},'problem_id':222,'language':'javascript'}
        value={'schema':'gamma.s-independent-mandatory-static-review.v1','candidate_executions':0,'static_failures':[],'static_reviewed_programs':1,'programs':[record]}
        self.assertFalse(p.accept_reviews(value,rows,contract)['222:javascript']['approved'])
        record.update(pins);self.assertTrue(p.accept_reviews(value,rows,contract)['222:javascript']['approved']) # control: correctly rebound record

    def test_scope_note_lineage_stays_on_original_source_review(self):
        self.assertIn("prepared['source_review_sha256']!=PRIOR_SOURCE_REVIEW_SHA",Path(p.__file__).read_text())


class FreezePolicy(unittest.TestCase):
    def policy(self):
        return {'schema':p.SCHEMA,'ids':list(p.IDS),'blocked_ids':list(p.BLOCKED),'profile_sha256':p.PROFILE_SHA,'source_manifest_sha256':p.MANIFEST_SHA,'limits':p.asdict(p.E.LIMITS),'argv':p.ARGV,'host_packet_bytes':p.PLAN.MAX_HOST_PACKET_BYTES,'plan_sha256':p.PLAN_SHA,'rerun':p.rerun_record()}

    def check_invalid(self,value,message):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'freeze.json';p.write(path,value)
            args=SimpleNamespace(freeze=path,freeze_sha256=p.sha(path.read_bytes()))
            with patch.object(p,'metadata') as metadata,patch.object(p.E.sandbox,'run') as run:
                with self.assertRaisesRegex(ValueError,message):p.verified(args,False)
                metadata.assert_not_called();run.assert_not_called()

    def test_v2_freeze_and_v1_profile_rejected(self):
        value=self.policy();value['schema']='gamma.s20-official-execution.v2';self.check_invalid(value,'fixed S execution policy')
        value=self.policy();value['profile_sha256']=p.PRIOR_PROFILE_SHA;self.check_invalid(value,'fixed S execution policy')

    def test_rerun_lineage_tamper_rejected(self):
        value=self.policy();value['rerun']['selection'].append([208,'javascript']);self.check_invalid(value,'rerun selection/lineage')
        value=self.policy();value['rerun']['checks_changed']=True;self.check_invalid(value,'rerun selection/lineage')

    def test_raised_limits_rejected(self):
        value=self.policy();value['limits']['cpu_seconds']=4;self.check_invalid(value,'fixed S execution policy')


class Dispatch(unittest.TestCase):
    def test_dispatch_uses_v2_observer_bytes_argv_and_limits(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve();body=b'// inert fixture bytes; sandbox is mocked, never executed\n'
            (root/'javascript').mkdir();(root/'javascript'/'222.js').write_bytes(body)
            rows={(222,'javascript'):{'path':'javascript/222.js','sha256':p.sha(body)}}
            data={222:[{'args':[{'values':[1],'left':[None],'right':[None],'root':0}],'expected':1}]};indices=[0]
            wire=p.PLAN.encoded(p.PLAN.packet(222,data[222],indices))
            entry={'indices':indices,'host_input_bytes':len(wire),'projected_output_bytes':{'python':8192,'javascript':8192},'mode':'synthetic'}
            value={'runtime':{'synthetic':True},'artifact_hashes':{'synthetic':'pin'},'plans':{'222':{'batches':[entry],'blocked_cases':[],'admitted_distinct_cases':1}},
                   'source_reviews':{'222:javascript':{'approved':True}},'execution_gate_sha256':'g','required_scope_blockers':{},'rerun':p.rerun_record()}
            seen=[]
            def run(argv,files,limits):
                seen.append((argv,files,limits));return p.E.sandbox.SandboxResult(exit_code=137,signal=9,stdout=b'',stderr=b'',wall_seconds=3.0)
            args=SimpleNamespace(output=root/'out',freeze_sha256='f',gate_sha256='g')
            with patch.object(p,'verified',return_value=(value,rows,{},data)),patch.object(p,'SOURCE',root),patch.object(p.E,'access'),patch.object(p.E.sandbox,'run',side_effect=run):
                p.run_or_replay(args)
            self.assertEqual(len(seen),1);argv,files,limits=seen[0]
            self.assertEqual(argv,p.ARGV['javascript']);self.assertIs(limits,p.E.LIMITS)
            self.assertEqual(set(files),{'program.cjs','inputs.json','harness.cjs','native_graphs.cjs'})
            for name in ('harness.cjs','native_graphs.cjs'):self.assertEqual(files[name],(p.OBSERVER/name).read_bytes())
            report=p.read_json(args.output/'report.json')
            self.assertEqual(report['rerun'],p.rerun_record())
            self.assertEqual(report['programs'][0]['failures'],[{'case':0,'reason':'sandbox_process_failure'}])


if __name__=='__main__':unittest.main()
