"""Bounded invented-input integration and terminal evidence fault tests."""
import contextlib
import copy
import hashlib
import io
import json
import lzma
import os
from pathlib import Path
import shutil
import signal
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import opcode_field_repair_gate_v1 as gate

PROJECT = Path(__file__).resolve().parents[1]
CLI = 'tools/opcode_field_repair_cli_v1.py'
CANDIDATE = 'opcode_field_repair250k_q0_v1'


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, sort_keys=True, indent=2) + '\n')


class GateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='opcode_field_gate_')
        cls.root = Path(cls.temp.name)
        cls.snapshot = cls.root/'snapshot'/CANDIDATE
        cls.snapshot.mkdir(parents=True)
        sources = {gate.SELF, gate.TESTS, gate.SHARED_DRIVER, gate.HARNESS_BASE, CLI}
        for source in sources:
            target = cls.root/source
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(PROJECT/source, target)
        for name in ('p', 'program.py', 'field_codec.py'):
            shutil.copyfile(PROJECT/'programs'/CANDIDATE/name, cls.snapshot/name)
        cls.raw = (b'<page><title>Oak</title><id>17</id><text xml:space="preserve">Oak Oak</text></page>\n'
                   b'\x00\x0f<title>x</title>\x00\xff') * 2
        cls.population = cls.root/'invented.raw'
        cls.population.write_bytes(cls.raw)
        legacy = {'__name__': 'untouched_synthetic_reference'}
        exec(lzma.decompress((cls.snapshot/'p').read_bytes(), format=2), legacy)
        archive = legacy['compress'](cls.raw)
        cls.plan = dict(schema=gate.SCHEMA, candidate_id=CANDIDATE, stage='development', arms=gate.ARMS,
                        population=cls.ref(cls.population), cli=cls.ref(cls.root/CLI),
                        source_files=[cls.ref(cls.root/s) for s in sorted(sources)],
                        package_files=[cls.ref(cls.snapshot/n) for n in ('p','program.py','field_codec.py')],
                        parent_package_files=[cls.ref(cls.snapshot/'p')], kernel_basis=[cls.ref(cls.root/gate.TESTS)],
                        runtime_files=[dict(path=str(Path(sys.executable).resolve()), bytes=Path(sys.executable).stat().st_size,
                                            sha256=gate.driver.sha(Path(sys.executable)))], resources=copy.deepcopy(gate.CAPS),
                        historical_parent=dict(archive_bytes=len(archive), archive_sha256=hashlib.sha256(archive).hexdigest()),
                        **gate.PHASE_CAPS)
        cls.contract_ref = dict(path='synthetic-contract.json', sha256='sha256:'+'a'*64)
        cls.gold = cls.root/'results'/'gold'
        cls.gold.mkdir(parents=True)
        with patch.object(gate, 'ROOT', cls.root), patch.object(gate.driver, 'ROOT', cls.root), \
             patch.object(gate, 'authenticate', return_value=({},cls.contract_ref,cls.plan,cls.snapshot)), \
             patch.dict(os.environ, {'GAMMA_RESOURCE_PHASE_MARKERS':str(cls.root/'gold.phases.jsonl')}), \
             contextlib.redirect_stdout(io.StringIO()):
            rc = gate.main(['--candidate','gold'])
        if rc:
            raise AssertionError((cls.gold/'stage-decision.json').read_text())
        write(cls.root/'recipe.json', dict(synthetic_only=True, corpus_bytes_opened=0,
              fixture=cls.ref(cls.population), fixture_hex=cls.raw.hex(), plan=cls.plan,
              sources=[cls.ref(cls.root/s) for s in sorted(sources)] + [cls.ref(cls.snapshot/n) for n in ('p','program.py','field_codec.py')]))

    @classmethod
    def tearDownClass(cls):
        if target := os.environ.get('OPCODE_FIELD_GATE_EVIDENCE_ZIP'):
            with zipfile.ZipFile(target, 'x', compression=zipfile.ZIP_DEFLATED) as bundle:
                for p in sorted(cls.root.rglob('*')):
                    if p.is_file() and (p == cls.root/'recipe.json' or p.parent == cls.gold or p.name == 'gold.phases.jsonl'):
                        bundle.write(p, str(p.relative_to(cls.root)))
        cls.temp.cleanup()

    @classmethod
    def ref(cls, path):
        return dict(path=str(path.relative_to(cls.root)), bytes=path.stat().st_size, sha256=gate.driver.sha(path))

    def setUp(self):
        self.name = self.id().rsplit('.',1)[-1]
        self.output = self.root/'results'/self.name
        self.output.mkdir()

    def fake_phase(self, directory, phase, argv, plan, marker):
        arm, operation = phase.split('-')
        suffix = '.raw' if operation == 'decode' else '.repeat.arc' if operation == 'repeat' else '.arc'
        Path(argv[4]).write_bytes((self.gold/(arm+suffix)).read_bytes())
        for suffix in ('.stdout','.stderr','.audit.json'):
            shutil.copyfile(self.gold/(phase+suffix), directory/(phase+suffix))
        record = json.loads((self.gold/(phase+'.execution.json')).read_text())
        record['argv'] = argv
        write(directory/(phase+'.execution.json'), record)
        return record

    def run_mocked(self, mutation=None, final_error=None):
        def phase(*args):
            result = self.fake_phase(*args)
            if mutation:
                mutation(args[0],args[1],args[2],result)
            return result
        replies = [({},self.contract_ref,self.plan,self.snapshot), final_error or ({},self.contract_ref,self.plan,self.snapshot)]
        with patch.object(gate,'ROOT',self.root), patch.object(gate.driver,'ROOT',self.root), \
             patch.object(gate,'authenticate',side_effect=replies), patch.object(gate.driver,'run_phase',side_effect=phase), \
             patch.dict(os.environ, {'GAMMA_RESOURCE_PHASE_MARKERS':str(self.root/(self.name+'.phases.jsonl'))}), \
             contextlib.redirect_stdout(io.StringIO()):
            rc = gate.main(['--candidate',self.name])
        return rc, json.loads((self.output/'stage-decision.json').read_text())

    def change_reports(self, arm, change, phases=('encode','decode','repeat')):
        def mutate(directory, phase, argv, record):
            if phase in [arm+'-'+p for p in phases]:
                path = directory/(phase+'.stdout')
                wrapper = json.loads(path.read_text())
                change(wrapper['result'])
                write(path, wrapper)
                write(directory/(phase+'.audit.json'), wrapper['result']['audit'])
        return mutate

    def failed(self, mutation=None, message=None, final_error=None):
        rc,stage = self.run_mocked(mutation,final_error)
        self.assertEqual(rc,1)
        self.assertFalse(stage['correctness_pass'])
        self.assertFalse((self.output/'costs-table.json').exists())
        self.assertFalse(json.loads((self.output/'artifacts.json').read_text())['complete'])
        if message:
            self.assertIn(message,stage['error'])
        return stage

    def test_ten_actual_phases_exact_inverse_raw_repeat_and_parent(self):
        stage = json.loads((self.gold/'stage-decision.json').read_text())
        self.assertEqual(stage['native_phases'],10)
        self.assertTrue(stage['correctness_pass'])
        self.assertEqual(len((self.root/'gold.phases.jsonl').read_text().splitlines()),20)
        self.assertEqual((self.gold/'P.arc').read_bytes(), (self.gold/'legacy.arc').read_bytes())
        self.assertEqual((self.gold/'P.arc').read_bytes(), (self.gold/'K.arc').read_bytes())
        for arm in ('P','K','D'):
            self.assertEqual((self.gold/(arm+'.raw')).read_bytes(),self.raw)
            self.assertEqual((self.gold/(arm+'.arc')).read_bytes(),(self.gold/(arm+'.repeat.arc')).read_bytes())
            reports = [json.loads((self.gold/(arm+'-'+p+'.stdout')).read_text())['result'] for p in ('encode','decode','repeat')]
            self.assertEqual(reports[0],reports[1]); self.assertEqual(reports[1],reports[2])
            repeat = next(r for r in stage['commands'] if r['phase'] == arm+'-repeat')
            self.assertEqual(Path(repeat['argv'][3]),self.gold/(arm+'.raw'))
        indexed = {r['path'] for r in json.loads((self.gold/'artifacts.json').read_text())['files']}
        self.assertEqual(indexed,{str(p.relative_to(self.root)) for p in self.gold.iterdir() if p.name not in ('artifacts.json','stage-decision.json')})

    def test_inverse_mismatch(self):
        def mutate(directory,phase,argv,record):
            if phase == 'D-decode': Path(argv[4]).write_bytes(b'wrong')
        self.failed(mutate,'independent raw inverse')

    def test_repeat_mismatch(self):
        def mutate(directory,phase,argv,record):
            if phase == 'D-repeat': Path(argv[4]).write_bytes(b'wrong')
        self.failed(mutate,'raw encoder repeat')

    def test_legacy_archive_mismatch(self):
        def mutate(directory,phase,argv,record):
            if phase == 'legacy-encode': Path(argv[4]).write_bytes(b'wrong')
        self.failed(mutate,'fresh retained parent')

    def test_same_arm_probability_disagreement(self):
        self.failed(self.change_reports('D',lambda r:r['audit'].update(probability_sha256='0'*64),('decode',)), 'decoder-common report')

    def test_same_arm_state_disagreement(self):
        self.failed(self.change_reports('D',lambda r:r['audit'].update(terminal_common_state_sha256='0'*64),('repeat',)), 'decoder-common report')

    def test_pk_projection_disagreement(self):
        self.failed(self.change_reports('K',lambda r:r['audit'].update(parent_projection_sha256='0'*64)), 'P/K authoritative')

    def test_pk_probability_disagreement(self):
        self.failed(self.change_reports('K',lambda r:r['audit'].update(probability_sha256='0'*64)), 'P/K authoritative')

    def test_audit_file_replacement(self):
        def mutate(directory,phase,argv,record):
            if phase == 'D-decode': write(directory/(phase+'.audit.json'),{})
        self.failed(mutate,'retained audit and report')

    def test_arm_value_accounting_overclaim(self):
        self.failed(self.change_reports('D',lambda r:r.update(complete_options_bytes=1)), 'arm value accounting')

    def test_zero_observer_events(self):
        self.failed(self.change_reports('D',lambda r:r['audit'].update(arithmetic_events=0)), 'synchronization counts')

    def test_missing_digest(self):
        self.failed(self.change_reports('D',lambda r:r['audit'].update(transition_sha256=None)), 'missing synchronization digest')

    def test_final_source_replacement(self):
        stage = self.failed(final_error=ValueError('source replaced'),message='Final authentication')
        self.assertFalse(stage['frozen_inputs_reverified'])
        self.assertEqual(stage['failure_class'],'infrastructure-failure')

    def test_phase_budget_stop(self):
        def mutate(directory,phase,argv,record):
            if phase == 'D-encode': record.update(returncode=-9,timeout=True)
        self.assertEqual(self.failed(mutate)['failure_class'],'budget-exhausted')

    def test_memory_budget_stop(self):
        def mutate(directory,phase,argv,record):
            if phase == 'D-encode':
                record.update(returncode=1)
                write(directory/(phase+'.stderr'),dict(error_class='budget-exhausted',error_type='MemoryError',error=''))
        self.assertEqual(self.failed(mutate)['failure_class'],'budget-exhausted')

    def test_file_budget_and_unknown_kill(self):
        last = dict(argv=['child'],timeout=False,error=None,returncode=-signal.SIGXFSZ)
        self.assertEqual(gate.classify_failure(ValueError('failure'),last,self.plan),'budget-exhausted')
        last['returncode'] = -signal.SIGKILL
        self.assertEqual(gate.classify_failure(ValueError('failure'),last,self.plan),'infrastructure-failure')

    def test_negative_size_is_valid_and_does_not_select(self):
        rows = [json.loads((self.gold/(a+'.result.json')).read_text()) for a in ('P','K','D')]
        rows[-1]['archive_bytes'] = rows[0]['archive_bytes']+1
        table = gate.comparison_table(rows,self.plan)
        self.assertEqual(table['archive_saving_bytes'],-1)
        self.assertFalse(table['validation_eligible'])
        self.assertFalse(table['confirmation_eligible'])
        self.assertIsNone(table['complete_package_bytes'])

    def test_validate_only_and_nonempty_output_never_launch(self):
        with patch.object(gate,'authenticate',return_value=({},self.contract_ref,self.plan,self.snapshot)), \
             patch.object(gate.driver,'run_phase') as child,contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(gate.main(['--candidate','synthetic','--validate-only']),0)
        child.assert_not_called()
        (self.output/'keep').write_bytes(b'keep')
        with patch.object(gate,'ROOT',self.root),patch.object(gate,'authenticate',return_value=({},self.contract_ref,self.plan,self.snapshot)), \
             patch.object(gate.driver,'run_phase') as child,self.assertRaisesRegex(ValueError,'nonempty output'):
            gate.main(['--candidate',self.name])
        child.assert_not_called()

    def test_snapshot_binding_and_unbound_file(self):
        revision = dict(files=[dict(path=p.name,bytes=p.stat().st_size,sha256=gate.driver.sha(p)) for p in self.snapshot.iterdir()])
        gate.verify_snapshot(self.snapshot,revision)
        bad = copy.deepcopy(revision); bad['files'][0]['sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError,'snapshot source differs'): gate.verify_snapshot(self.snapshot,bad)
        with self.assertRaisesRegex(ValueError,'unbound files'): gate.verify_snapshot(self.snapshot,dict(files=revision['files'][:-1]))

    def test_snapshot_package_does_not_read_mutable_worktree(self):
        row = dict(path='programs/'+CANDIDATE+'/p',bytes=(self.snapshot/'p').stat().st_size,sha256=gate.driver.sha(self.snapshot/'p'))
        with patch.object(gate,'ROOT',self.root):
            self.assertEqual(gate.check_file(row,snapshot=self.snapshot,candidate=CANDIDATE),self.snapshot/'p')


if __name__ == '__main__':
    unittest.main()
