"""Test the parity runner against retained synthetic evidence, never corpus."""
import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import opcode_field_compact_gate_v1 as gate


class GateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=ROOT/'results',prefix='compact-runner-unit-')
        self.addCleanup(self.tmp.cleanup)
        self.directory=Path(self.tmp.name)

    def test_actual_four_phase_synthetic_replay(self):
        retained=ROOT/'results/opcode_field_compact_unit_20260908/attempt01/retained'
        row={'name':'synthetic','input':gate.phase.artifact(retained/'fixture.raw'),
             'archive':gate.phase.artifact(retained/'observed.arc'),
             'audit':gate.phase.artifact(retained/'encode.audit.json')}
        result=gate.run_population(self.directory,row,ROOT/'programs'/gate.CID,
                                  self.directory/'phases.jsonl',
                                  dict(phase_cpu_seconds=60,phase_wall_seconds=90,phase_address_bytes=2147483648))
        self.assertEqual(result['archive_bytes'],27)
        self.assertEqual(len(result['commands']),4)
        self.assertTrue(result['complete_state_witness_identity'])
        self.assertEqual(result['artifacts']['encode']['sha256'],result['artifacts']['repeat']['sha256'])

    def test_archive_divergence_retained(self):
        with self.assertRaises(ValueError):
            gate.compare(b'abc',b'abx',self.directory,'bytes')
        d=gate.phase.read_json(self.directory/'bytes.divergence.json')
        self.assertEqual(d['first_divergence_byte'],2)

    def test_shared_state_divergence_retained(self):
        with self.assertRaises(ValueError):
            gate.compare({'checkpoints':[{'prob':'a'}]},{'checkpoints':[{'prob':'b'}]},self.directory,'state')
        d=gate.phase.read_json(self.directory/'state.divergence.json')
        self.assertEqual(d['path'],'$.checkpoints[0].prob')

    def test_phase_failure_classes(self):
        record=dict(returncode=0,timeout=False,error=None)
        gate.require_phase(record)
        for code in (-9,-24,-25,124,137):
            with self.assertRaises(gate.BudgetStop):gate.require_phase(dict(record,returncode=code))
        with self.assertRaises(gate.BudgetStop):gate.require_phase(dict(record,returncode=1),'Traceback\nMemoryError\n')
        with self.assertRaises(OSError):gate.require_phase(dict(record,error='process vanished'))
        with self.assertRaises(ValueError):gate.require_phase(dict(record,returncode=1))

    def test_optional_telemetry_does_not_mask_valid_artifacts(self):
        retained=ROOT/'results/opcode_field_compact_unit_20260908/attempt01/retained'
        row={'name':'telemetry','input':gate.phase.artifact(retained/'fixture.raw'),
             'archive':gate.phase.artifact(retained/'observed.arc'),
             'audit':gate.phase.artifact(retained/'encode.audit.json')}
        original=gate.phase.read_json
        def read(path):
            if str(path).endswith('.stdout'):raise ValueError('optional telemetry absent')
            return original(path)
        with mock.patch.object(gate.phase,'read_json',side_effect=read):
            result=gate.run_population(self.directory,row,ROOT/'programs'/gate.CID,self.directory/'phases.jsonl',
                                      dict(phase_cpu_seconds=60,phase_wall_seconds=90,phase_address_bytes=2147483648))
        self.assertTrue(result['exact_inverse'])
        self.assertTrue(all(x['codec_resources'] is None and x['missing_diagnostics'] for x in result['commands']))

    def test_missing_mandatory_witness_fails(self):
        retained=ROOT/'results/opcode_field_compact_unit_20260908/attempt01/retained'
        row={'name':'missing','input':gate.phase.artifact(retained/'fixture.raw'),
             'archive':gate.phase.artifact(retained/'observed.arc'),
             'audit':dict(path=str((self.directory/'absent').relative_to(ROOT)))}
        with self.assertRaises(FileNotFoundError):
            gate.run_population(self.directory,row,ROOT/'programs'/gate.CID,self.directory/'phases.jsonl')

    def test_plan_rejects_changed_population_and_resource_bounds(self):
        sources=[gate.SELF,gate.CLI,'tools/opcode_field_repair_cli_v1.py','tools/dualstream_grammar_gate_v1.py',
                 'tools/dualstream_grammar_v1.py','tools/opcode_field_repair_gate_v2.py',
                 'tests/test_opcode_field_compact_gate_v1.py','tools/research_contracts.py']
        plan=dict(candidate_id=gate.CID,resources=gate.CAPS,phase_resources=gate.PHASES,
                  populations=[dict(name=n,input=dict(bytes=b,sha256=h)) for n,b,h in gate.POPULATIONS],
                  source_files=[dict(path=p) for p in sources],runtime_files=[{}],evidence=[{}],
                  package_files=[dict(path='programs/'+gate.CID+'/'+p) for p in ('p','program.py')])
        gate.validate_plan(plan)
        for key in ('runtime_files','evidence'):
            changed=copy.deepcopy(plan);changed[key]=[]
            with self.assertRaises(ValueError):gate.validate_plan(changed)
        changed=copy.deepcopy(plan);changed['resources']['cpus']=[1]
        with self.assertRaises(ValueError):gate.validate_plan(changed)
        changed=copy.deepcopy(plan);changed['populations'][0]['input']['sha256']='0'*64
        with self.assertRaises(ValueError):gate.validate_plan(changed)


if __name__=='__main__':unittest.main(verbosity=2)
