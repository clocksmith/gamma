"""Synthetic process-output tests for the observed gate; no native/corpus launch."""
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import midas_open_observed_gate_v1 as runner


def digest(data): return hashlib.sha256(data).hexdigest()


class FixtureGate:
    def __init__(self,root):
        self.result=root/'result';self.result.mkdir();self.required=set();self.binaries={};self.commands=[]
        self.raw=b'x';self.population=root/'raw';self.population.write_bytes(self.raw)
        self.programs={name:root/name for name in ('parent','observer')}
        for name,path in self.programs.items():path.write_bytes(name.encode())
        self.mutation=None;self.fail_phase=None

    def write(self,name,value):
        (self.result/name).write_text(json.dumps(value))

    def artifact(self,path):
        data=path.read_bytes();return {'path':str(path),'bytes':len(data),'sha256':digest(data)}

    def run(self,name,argv,cap):
        if name==self.fail_phase:
            self.commands.append({'phase':name,'returncode':124})
            raise TimeoutError('fixture elapsed stop')
        observed=argv[0]==str(self.programs['observer'])
        operation,arm=argv[1:3];output=Path(argv[5]);output.mkdir()
        archive=(b'P' if arm in 'PK' else arm.encode())*({'P':7,'K':7,'F':6,'S':8}[arm])
        blobs=[arm.encode(),b'parent' if arm in 'PK' else arm.encode(),b'coder',b'reference' if arm in 'PK' else arm.encode()]
        state=b'GMST\1';ranges={}
        for key,blob in zip(runner.base.STATE_NAMES,blobs):
            state+=struct.pack('<Q',len(blob));ranges[key]=(len(state),len(blob));state+=blob
        (output/'state.bin').write_bytes(state)
        (output/'data').write_bytes(self.raw if operation=='decode' else archive)
        summary={'schema':'midas_open_boundary_observer_v1' if observed else 'midas_open_codec_operation_v1',
                 'operation':operation,'arm':arm,'frontend':'raw_identity_v1','raw_bytes':1,'max_raw_bytes':1,
                 'archive_bytes':len(archive),'state_bytes':len(state),'model_updates':0,'objective_credit_bytes':0,'resource_qualified':False}
        if observed:
            probabilities=b'MOPROB01'+struct.pack('<QIB',1,0x4F504601,1 if arm=='F' else 2 if arm=='S' else 0)+struct.pack('<8H',*[32768]*8)
            (output/'probabilities.bin').write_bytes(probabilities)
            rows=[]
            for kind,position in [('initial',0),('final',8)]:
                parts=[]
                for key in runner.observer.PART_NAMES:
                    start,size=(0,len(state)) if key=='complete_state' else ranges.get(key,(0,1))
                    parts.append({'name':key,'offset':start,'bytes':size,'sha256':digest(state[start:start+size])})
                rows.append({'kind':kind,'bit_position':position,'parts':parts,'model_updates':0,'parent_updates':0,'midpoint_updates':0,'shadow_updates':0})
            boundary=''.join(json.dumps(row)+'\n' for row in rows).encode()
            (output/'boundaries.jsonl').write_bytes(boundary);(output/'snapshots.bin').write_bytes(b'MOSNAP01\0')
            summary.update(probability_records=8,boundary_records=2,probability_bytes=len(probabilities),boundary_bytes=len(boundary),snapshot_bytes=9,exact_snapshots=False)
        (output/'summary.json').write_text(json.dumps(summary))
        self.write(name+'.stdout',summary)
        self.commands.append({'phase':name,'returncode':0,'elapsed_seconds':0.1,'user_cpu_seconds':0.1,'system_cpu_seconds':0.0})
        if self.mutation:self.mutation(name,output)


class ObservedGateTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.gate=FixtureGate(Path(self.tmp.name))

    def run_matrix(self):
        return runner.compare_matrix(self.gate,self.gate.programs,self.gate.population,1)

    def test_sixteen_phases_preserve_reference_and_observed_boundaries(self):
        result=self.run_matrix()
        self.assertEqual(len(self.gate.commands),16)
        self.assertTrue(result['all_reference_archives_equal'])
        self.assertTrue(result['all_reference_final_states_equal'])
        self.assertTrue(result['all_boundaries_equal'])
        self.assertTrue(result['pk_identity'])
        self.assertEqual(result['F_vs_P_archive_saved_bytes'],1)
        self.assertEqual(len(list(self.gate.result.glob('*comparison.json'))),13)

    def test_changed_reference_archive_fails_after_independent_replay(self):
        def mutate(name,path):
            if name=='P-reference':(path/'data').write_bytes(b'changed')
        self.gate.mutation=mutate
        with self.assertRaises(runner.base.EvidenceFailure):self.run_matrix()

    def test_intermediate_probability_corruption_blocks_result(self):
        def mutate(name,path):
            if name=='F-decode':
                target=path/'probabilities.bin';data=bytearray(target.read_bytes());data[23]^=1;target.write_bytes(data)
        self.gate.mutation=mutate
        with self.assertRaisesRegex(runner.base.EvidenceFailure,'boundary/probability divergence'):self.run_matrix()
        result=json.loads((self.gate.result/'F-decode-comparison.json').read_text())
        self.assertEqual(result['kind'],'probability');self.assertEqual(result['bit_position'],1)

    def test_missing_boundary_cannot_pass_on_final_state_alone(self):
        def mutate(name,path):
            if name=='P-encode':
                target=path/'boundaries.jsonl';target.write_bytes(target.read_bytes().splitlines(keepends=True)[-1])
        self.gate.mutation=mutate
        with self.assertRaisesRegex(ValueError,'boundary coordinates'):self.run_matrix()

    def test_budget_stop_is_not_compression_rejection(self):
        self.gate.fail_phase='K-decode'
        with self.assertRaises(TimeoutError) as caught:self.run_matrix()
        self.assertEqual(runner.base.classify(caught.exception,self.gate.commands),'budget_exhausted')
        self.assertEqual(self.gate.commands[-1]['phase'],'K-decode')

    def test_plan_requires_both_builds_and_explicit_bounds(self):
        plan={'schema':runner.PLAN_SCHEMA,'candidate_id':'unit','population':{'bytes':4096},'population_kind':'synthetic',
              'builds':{'parent':{},'observer':{}},'runtime_files':[{'path':'/bound'}],
              'resources':{'cpus':[2],'memory_bytes':2147483648,'scratch_bytes':268435456,'swap_bytes':0,'wall_seconds':600},'phase_wall_seconds':120}
        runner.validate_plan(plan,'unit')
        plan['builds'].pop('parent')
        with self.assertRaises(runner.base.EvidenceFailure):runner.validate_plan(plan,'unit')
        plan['builds']['parent']={};plan['phase_wall_seconds']=121
        with self.assertRaises(runner.base.EvidenceFailure):runner.validate_plan(plan,'unit')


if __name__=='__main__':unittest.main()
