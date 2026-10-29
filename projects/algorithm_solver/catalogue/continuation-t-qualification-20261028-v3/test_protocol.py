"""T16 v3 rerun controller: source-free binding/selection/fail-closed controls.

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
V1_OBSERVER=HERE.parent/'continuation-t-observers-20261028-v1'


def load_v2_controller():
    spec=importlib.util.spec_from_file_location('t16_v2_controller_for_comparison',HERE.parent/'continuation-t-qualification-20261028-v2/protocol.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


class ObserverBinding(unittest.TestCase):
    def test_profile_is_observer_v2_with_v1_lineage(self):
        self.assertEqual(p.OBSERVER.name,'continuation-t-observers-20261028-v2')
        self.assertEqual(p.sha((p.OBSERVER/'native-bindings.json').read_bytes()),p.PROFILE_SHA)
        self.assertEqual(p.PROFILE['previous_profile_sha256'],p.PRIOR_PROFILE_SHA)
        self.assertEqual(p.sha((V1_OBSERVER/'native-bindings.json').read_bytes()),p.PRIOR_PROFILE_SHA)
        self.assertEqual(p.PROFILE['route'],'official-t-v1') # record route is unchanged

    def test_only_javascript_observer_bytes_change(self):
        v1={r['path']:r['sha256'] for r in json.loads((V1_OBSERVER/'native-bindings.json').read_text())['files']}
        for name in ('harness.py','native_graphs.py','host_check.py','plan.py','prospective-plan.json'):
            self.assertEqual(p.PROFILE_FILES[name],v1[name],name)
        for name in ('harness.cjs','native_graphs.cjs'):
            self.assertNotEqual(p.PROFILE_FILES[name],v1[name],name)
            self.assertEqual(p.sha((p.OBSERVER/name).read_bytes()),p.PROFILE_FILES[name])

    def test_argv_limits_plan_and_checker_unchanged_from_v2_controller(self):
        v2=load_v2_controller()
        self.assertEqual(p.ARGV,v2.ARGV);self.assertEqual(p.asdict(p.E.LIMITS),p.asdict(v2.E.LIMITS))
        self.assertEqual(p.E.LIMITS.cpu_seconds,3);self.assertEqual(p.E.LIMITS.wall_seconds,8);self.assertEqual(p.E.LIMITS.memory_bytes,1024**3)
        self.assertEqual(p.PLAN_SHA,v2.PLAN_SHA);self.assertEqual(p.MANIFEST_SHA,v2.MANIFEST_SHA)
        self.assertEqual(p.sha(Path(p.CHECK.__file__).read_bytes()),p.sha(Path(v2.CHECK.__file__).read_bytes()))
        self.assertEqual(p.sha(Path(p.PLAN.__file__).read_bytes()),p.sha(Path(v2.PLAN.__file__).read_bytes()))
        self.assertEqual(p.PRIOR_SOURCE_REVIEW_SHA,v2.SOURCE_REVIEW_SHA);self.assertEqual(p.PRIOR_PROFILE_SHA,v2.PROFILE_SHA)

    def test_no_historical_stress_exception_remains(self):
        self.assertEqual(p.ARCHIVED_STRESS_FILES,frozenset());self.assertEqual(p.historical_stress_evidence(),{})
        with tempfile.TemporaryDirectory() as directory,patch.object(p,'OBSERVER',Path(directory)):
            with self.assertRaises(FileNotFoundError):p.profile_file_status('stress-tree.stdout.jsonl','pin')


class Selection(unittest.TestCase):
    def test_exact_rerun_selection_after_full_inventory(self):
        rows,_=p.metadata()
        self.assertEqual(tuple(rows),p.RERUN)
        self.assertEqual(p.RERUN,((234,'javascript'),(235,'javascript'),(236,'javascript')))

    def test_missing_rerun_slot_rejected(self):
        with patch.object(p,'RERUN',p.RERUN+((999,'javascript'),)):
            with self.assertRaisesRegex(ValueError,'exact rerun selection'):p.metadata()


class ReviewsFailClosed(unittest.TestCase):
    def test_no_review_approves_nothing(self):
        rows,contract=p.metadata()
        result=p.reviews(SimpleNamespace(review=None),rows,contract)
        self.assertEqual(set(result),{f'{pid}:{lang}' for pid,lang in p.RERUN})
        self.assertFalse(any(r['approved'] for r in result.values()))

    def test_unpinned_or_mismatched_receipt_refused(self):
        self.assertEqual(p.SOURCE_REVIEW_SHA,'512afc450b9242977ad55b4c8613619e95e17990f52278f0efd9a0ec78a2303c')
        rows,contract=p.metadata()
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'review.json';path.write_text('{}')
            with self.assertRaisesRegex(ValueError,'exact independent T16 source review required'):p.reviews(SimpleNamespace(review=path),rows,contract)
            with self.assertRaisesRegex(ValueError,'exact independent observer/source receipt required'):p.observer_review(SimpleNamespace(review=path))
            original=p.SOURCE_REVIEW_SHA
            try:
                p.SOURCE_REVIEW_SHA=None
                with self.assertRaisesRegex(ValueError,'not yet pinned'):p.reviews(SimpleNamespace(review=path),rows,contract)
            finally:p.SOURCE_REVIEW_SHA=original

    def test_old_v1_bound_review_cannot_approve_v2_binding(self):
        rows,contract=p.metadata()
        for pid,lang in p.RERUN:
            pins=p.binding(pid,lang,rows[pid,lang],contract)
            self.assertEqual(pins['observer_profile_sha256'],p.PROFILE_SHA)
            self.assertNotEqual(pins['observer_profile_sha256'],p.PRIOR_PROFILE_SHA)
        record={**pins,'observer_profile_sha256':p.PRIOR_PROFILE_SHA,'reviewer':'synthetic',**{flag:True for flag in p.FLAGS},'problem_id':pid,'language':lang}
        value={'schema':'gamma.independent-source-observer-static-review.v1','candidate_executions':0,'observer_profile_sha256':p.PROFILE_SHA,'source_manifest_sha256':p.MANIFEST_SHA,'blocked_ids':list(p.BLOCKED),'blocked_ids_opened':False,'selected_programs':len(rows),'programs':[record]}
        self.assertFalse(p.accept_reviews(value,rows,contract)[f'{pid}:{lang}']['approved'])


class FreezePolicy(unittest.TestCase):
    def policy(self):
        return {'schema':p.SCHEMA,'ids':list(p.IDS),'blocked_ids':list(p.BLOCKED),'profile_sha256':p.PROFILE_SHA,'source_manifest_sha256':p.MANIFEST_SHA,'limits':p.asdict(p.E.LIMITS),'argv':p.ARGV,'host_packet_bytes':p.PLAN.MAX_HOST_PACKET_BYTES,'plan_sha256':p.PLAN_SHA,'historical_helper_stress_evidence':p.historical_stress_evidence(),'historical_helper_stress_used_for_qualification':False,'rerun':p.rerun_record()}

    def check_invalid(self,value,message):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'freeze.json';p.write(path,value)
            args=SimpleNamespace(freeze=path,freeze_sha256=p.sha(path.read_bytes()))
            with patch.object(p,'metadata') as metadata,patch.object(p.E.sandbox,'run') as run:
                with self.assertRaisesRegex(ValueError,message):p.verified(args,False)
                metadata.assert_not_called();run.assert_not_called()

    def test_v2_freeze_and_v1_profile_rejected(self):
        value=self.policy();value['schema']='gamma.t16-official-execution.v2';self.check_invalid(value,'fixed T execution policy')
        value=self.policy();value['profile_sha256']=p.PRIOR_PROFILE_SHA;self.check_invalid(value,'fixed T execution policy')

    def test_rerun_lineage_tamper_rejected(self):
        value=self.policy();value['rerun']['selection'].append([233,'javascript']);self.check_invalid(value,'rerun selection/lineage')
        value=self.policy();value['rerun']['limits_changed']=True;self.check_invalid(value,'rerun selection/lineage')

    def test_raised_limits_rejected(self):
        value=self.policy();value['limits']['cpu_seconds']=4;self.check_invalid(value,'fixed T execution policy')


class Dispatch(unittest.TestCase):
    def test_dispatch_uses_v2_observer_bytes_argv_and_limits(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve();body=b'// inert fixture bytes; sandbox is mocked, never executed\n'
            (root/'javascript').mkdir();(root/'javascript'/'234.js').write_bytes(body)
            rows={(234,'javascript'):{'path':'javascript/234.js','sha256':p.sha(body)}}
            data={234:[{'args':[{'values':[1],'next':[None],'head':0}],'expected':True}]};indices=[0]
            wire=p.PLAN.encoded(p.PLAN.packet(234,data[234],indices))
            entry={'indices':indices,'host_input_bytes':len(wire),'projected_output_bytes':{'python':8192,'javascript':8192},'mode':'synthetic'}
            value={'runtime':{'synthetic':True},'artifact_hashes':{'synthetic':'pin'},'plans':{'234':{'batches':[entry],'blocked_cases':[],'admitted_distinct_cases':1}},
                   'source_reviews':{'234:javascript':{'approved':True}},'execution_gate_sha256':'g','historical_helper_stress_evidence':{},'historical_helper_stress_used_for_qualification':False,'rerun':p.rerun_record()}
            seen=[]
            def run(argv,files,limits):
                seen.append((argv,files,limits))
                return p.E.sandbox.SandboxResult(exit_code=137,signal=9,stdout=b'',stderr=b'',wall_seconds=3.0)
            args=SimpleNamespace(output=root/'out',freeze_sha256='f',gate_sha256='g')
            with patch.object(p,'verified',return_value=(value,rows,{},data)),patch.object(p,'SOURCE',root),patch.object(p.E,'access'),patch.object(p.E.sandbox,'run',side_effect=run):
                result=p.run_or_replay(args)
            self.assertEqual(len(seen),1);argv,files,limits=seen[0]
            self.assertEqual(argv,p.ARGV['javascript']);self.assertIs(limits,p.E.LIMITS)
            self.assertEqual(set(files),{'program.cjs','inputs.json','harness.cjs','native_graphs.cjs'})
            for name in ('harness.cjs','native_graphs.cjs'):self.assertEqual(files[name],(p.OBSERVER/name).read_bytes())
            report=p.read_json(args.output/'report.json')
            self.assertEqual(report['rerun'],p.rerun_record());self.assertEqual(result['programs'],1)
            self.assertEqual(report['programs'][0]['failures'],[{'case':0,'reason':'sandbox_process_failure'}]) # a killed batch stays a failure


if __name__=='__main__':unittest.main()
