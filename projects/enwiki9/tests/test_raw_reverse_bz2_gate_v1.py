"""Invented fixtures and bounded driver fault tests; no corpus reads."""
import bz2
import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import random
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import raw_reverse_bz2_gate_v1 as gate
from tools import raw_reverse_bz2_v1 as codec

PROJECT = Path(__file__).resolve().parents[1]


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')


class GateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='raw_reverse_bz2_gate_')
        cls.root = Path(cls.temp.name)
        sources = {gate.SELF, gate.SHARED_DRIVER, gate.HARNESS_BASE, gate.BASELINE, gate.TESTS, *gate.PACKAGE}
        for source in sources:
            target = cls.root/source
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(PROJECT/source, target)
        rng, value, walk = random.Random(871), 0, bytearray()
        for _ in range(8192):
            value = (value+rng.choice([-1, 0, 1])) % 256
            walk.append(value)
        cls.raws = dict(walk=bytes(walk), arbitrary=random.Random(491).randbytes(2048))
        cls.plans, cls.golds = {}, {}
        cls.contract_ref = dict(path='operations/adaptive/experiments/synthetic.json', sha256='sha256:'+'a'*64)
        for name, raw in cls.raws.items():
            population = cls.root/'inputs'/name/'raw.bin'
            population.parent.mkdir(parents=True)
            population.write_bytes(raw)
            plan = dict(schema=gate.SCHEMA, candidate_id=name, stage='development', arms=gate.ARMS,
                population=cls.ref(population), block_size=250000,
                resources=dict(cpus=[2], memory_bytes=1073741824, scratch_bytes=67108864, swap_bytes=0, wall_seconds=300),
                phase_cpu_seconds=60, phase_wall_seconds=90, phase_address_bytes=536870912,
                transform_spec=codec.TRANSFORM_SPEC, kernel_basis='Fixed invented fixtures only',
                runtime_files=[dict(path=str(Path(sys.executable).resolve()), bytes=Path(sys.executable).stat().st_size,
                                    sha256=gate.driver.sha(Path(sys.executable)))])
            gold = cls.root/'results'/('gold_'+name)
            gold.mkdir(parents=True)
            with patch.object(gate, 'ROOT', cls.root), patch.object(gate.driver, 'ROOT', cls.root), \
                 patch.object(gate, 'authenticate', return_value=({}, cls.contract_ref, plan)), \
                 patch.dict(os.environ, {'GAMMA_RESOURCE_PHASE_MARKERS': str(cls.root/(name+'.phases.jsonl'))}), \
                 contextlib.redirect_stdout(io.StringIO()):
                rc = gate.main(['--candidate', gold.name])
            if rc:
                raise AssertionError((gold/'stage-decision.json').read_text())
            cls.plans[name], cls.golds[name] = plan, gold
        write(cls.root/'recipe.json', dict(synthetic_only=True, corpus_bytes_opened=0,
            walk='Random871;8192 steps; initial0 then add choice(-1,0,1) modulo256', arbitrary='Random491.randbytes(2048)',
            source_files=[cls.ref(cls.root/p) for p in sorted(sources)],
            fixtures={n: dict(bytes=len(r), sha256=hashlib.sha256(r).hexdigest()) for n, r in cls.raws.items()}))

    @classmethod
    def tearDownClass(cls):
        if target := os.environ.get('RAW_REVERSE_GATE_EVIDENCE_ZIP'):
            with zipfile.ZipFile(target, 'x', compression=zipfile.ZIP_DEFLATED) as bundle:
                for p in sorted(cls.root.rglob('*')):
                    if p.is_file() and (p == cls.root/'recipe.json' or p.parts[-2] in ('gold_walk', 'gold_arbitrary')
                                        or p.suffix == '.jsonl' and p.parent == cls.root):
                        bundle.write(p, str(p.relative_to(cls.root)))
        cls.temp.cleanup()

    @classmethod
    def ref(cls, path):
        data = path.read_bytes()
        return dict(path=str(path.relative_to(cls.root)), bytes=len(data), sha256=hashlib.sha256(data).hexdigest())

    def setUp(self):
        self.name = self.id().rsplit('.', 1)[-1]
        self.output = self.root/'results'/self.name
        self.output.mkdir()
        self.plan, self.gold = self.plans['walk'], self.golds['walk']

    def fake_phase(self, directory, phase, argv, plan, marker):
        arm, operation = phase.split('-')
        suffix = '.raw' if operation == 'decode' else '.repeat.rbz' if operation == 'repeat' else '.rbz'
        Path(argv[4]).write_bytes((self.gold/(arm+suffix)).read_bytes())
        for suffix in ('.stdout', '.stderr'):
            shutil.copyfile(self.gold/(phase+suffix), directory/(phase+suffix))
        record = json.loads((self.gold/(phase+'.execution.json')).read_text())
        record['argv'] = argv
        write(directory/(phase+'.execution.json'), record)
        return record

    def run_mocked(self, mutation=None, final_error=None):
        def phase(*args):
            record = self.fake_phase(*args)
            if mutation:
                mutation(args[0], args[1], args[2], record)
            return record
        replies = [({}, self.contract_ref, self.plan), final_error or ({}, self.contract_ref, self.plan)]
        with patch.object(gate, 'ROOT', self.root), patch.object(gate.driver, 'ROOT', self.root), \
             patch.object(gate, 'authenticate', side_effect=replies), patch.object(gate.driver, 'run_phase', side_effect=phase), \
             patch.dict(os.environ, {'GAMMA_RESOURCE_PHASE_MARKERS': str(self.root/(self.name+'.phases.jsonl'))}), \
             contextlib.redirect_stdout(io.StringIO()):
            rc = gate.main(['--candidate', self.name])
        return rc, json.loads((self.output/'stage-decision.json').read_text())

    def change_reports(self, arm, change, phases=('encode', 'decode', 'repeat')):
        def mutation(directory, phase, argv, record):
            if phase in [arm+'-'+p for p in phases]:
                p = directory/(phase+'.stdout')
                wrapper = json.loads(p.read_text())
                change(wrapper['result'])
                write(p, wrapper)
        return mutation

    def failed(self, mutation=None, message=None, final_error=None):
        rc, stage = self.run_mocked(mutation, final_error)
        self.assertEqual(rc, 1)
        self.assertFalse(stage['correctness_pass'])
        self.assertFalse((self.output/'costs-table.json').exists())
        self.assertFalse(json.loads((self.output/'artifacts.json').read_text())['complete'])
        if message:
            self.assertIn(message, stage['error'])
        return stage

    def test_eighteen_actual_phases_inverse_repeat_and_fresh_p(self):
        for name, gold in self.golds.items():
            stage = json.loads((gold/'stage-decision.json').read_text())
            self.assertTrue(stage['correctness_pass'])
            self.assertEqual(stage['native_phases'], 9)
            table = stage['costs']
            self.assertEqual(table['strict_d_improvement'], table['archive_bytes']['D'] < table['archive_bytes']['P'])
            self.assertTrue(table['forced_treatment'])
            self.assertTrue(table['fresh_p_measured'])
            self.assertFalse(table['historical_baseline_used'])
            self.assertEqual((gold/'P.rbz').read_bytes(), (gold/'K.rbz').read_bytes())
            self.assertEqual(len((self.root/(name+'.phases.jsonl')).read_text().splitlines()), 18)
            for arm in ('P', 'K', 'D'):
                self.assertEqual((gold/(arm+'.raw')).read_bytes(), self.raws[name])
                archive = (gold/(arm+'.rbz')).read_bytes()
                self.assertEqual(archive, (gold/(arm+'.repeat.rbz')).read_bytes())
                self.assertEqual(archive[gate.HEADER.size+gate.FRAME.size:], bz2.compress(self.raws[name][::-1] if arm == 'D' else self.raws[name], compresslevel=9))
                row = json.loads((gold/(arm+'.result.json')).read_text())
                self.assertEqual(sum(row['accounting'].values()), row['archive_bytes'])
                self.assertEqual(row['reversed_frames'], int(arm == 'D'))
                repeat = next(r for r in stage['commands'] if r['phase'] == arm+'-repeat')
                self.assertEqual(Path(repeat['argv'][3]), gold/(arm+'.raw'))
                self.assertEqual(repeat['argv'][2], 'encode')
            indexed = {r['path'] for r in json.loads((gold/'artifacts.json').read_text())['files']}
            self.assertEqual(indexed, {str(p.relative_to(self.root)) for p in gold.iterdir() if p.name not in ('artifacts.json', 'stage-decision.json')})

    def test_forced_growth_remains_valid_measurement(self):
        rows = [json.loads((self.gold/(a+'.result.json')).read_text()) for a in ('P', 'K', 'D')]
        rows[2]['archive_bytes'] = rows[0]['archive_bytes']+1
        with patch.object(gate, 'ROOT', self.root):
            table = gate.comparison_table(rows, self.plan)
        self.assertEqual(table['p_minus_d_bytes'], -1)
        self.assertFalse(table['confirmation_eligible'])

    def test_p_k_byte_drift(self):
        def mutate(directory, phase, argv, record):
            if phase in ('K-encode', 'K-repeat'):
                with Path(argv[4]).open('ab') as stream:
                    stream.write(b'x')
        self.failed(mutate, 'P/K archive identity')

    def test_raw_inverse_corruption(self):
        def mutate(directory, phase, argv, record):
            if phase == 'K-decode':
                Path(argv[4]).write_bytes(b'wrong')
        self.failed(mutate, 'independent inverse')

    def test_repeat_archive_corruption(self):
        def mutate(directory, phase, argv, record):
            if phase == 'D-repeat':
                with Path(argv[4]).open('ab') as stream:
                    stream.write(b'x')
        self.failed(mutate, 'raw encoder repeat')

    def test_repeat_report_drift(self):
        self.failed(self.change_reports('D', lambda r:r.update(raw_sha256='0'*64), ('repeat',)), 'raw encoder repeat report')

    def test_decoder_projection_drift(self):
        self.failed(self.change_reports('D', lambda r:r['frames'][0].update(coded_bytes_sha256='0'*64), ('decode',)), 'independent decoder projection')

    def test_raw_hash_corruption(self):
        self.failed(self.change_reports('D', lambda r:r.update(raw_sha256='0'*64)), 'population identity')

    def test_direction_must_be_forced(self):
        self.failed(self.change_reports('D', lambda r:r['frames'][0].update(direction=0)), 'direction differs')

    def test_coded_input_hash_corruption(self):
        self.failed(self.change_reports('D', lambda r:r['frames'][0].update(coded_bytes_sha256='0'*64)), 'coded byte identity')

    def test_global_accounting_corruption(self):
        self.failed(self.change_reports('D', lambda r:r['costs'].update(framing=0)), 'complete archive accounting')

    def test_frame_accounting_corruption(self):
        self.failed(self.change_reports('D', lambda r:r['frames'][0]['costs'].update(framing=0)), 'frame accounting')

    def test_package_overclaim_rejected(self):
        self.failed(self.change_reports('D', lambda r:r.update(complete_package_bytes=0)), 'unsupported result package')

    def test_final_reauthentication_failure_blocks_table(self):
        stage = self.failed(final_error=ValueError('source replaced'), message='Final authentication')
        self.assertFalse(stage['frozen_inputs_reverified'])
        self.assertEqual(stage['failure_class'], 'infrastructure-failure')

    def test_projection_excludes_only_mode(self):
        enc = json.loads((self.gold/'D-encode.stdout').read_text())['result']
        dec = json.loads((self.gold/'D-decode.stdout').read_text())['result']
        self.assertEqual(gate.common_report(enc), dec)
        enc['hidden_dependency'] = True
        self.assertNotEqual(gate.common_report(enc), dec)

    def test_plan_identity_bounds_and_fresh_selection(self):
        plan = copy.deepcopy(self.plan)
        plan['candidate_id'] = 'shape'
        plan['population'].update(bytes=250000, sha256=gate.OPENING_SHA)
        gate.validate_plan(plan, 'shape')
        for change in (lambda p:p['transform_spec'].update(direction='tokens'), lambda p:p.update(block_size=65536),
                       lambda p:p.update(phase_cpu_seconds=True), lambda p:p['population'].update(path='../raw'),
                       lambda p:p.update(plain_archive={}), lambda p:p.update(stage='confirmation')):
            p = copy.deepcopy(plan)
            change(p)
            with self.assertRaises(ValueError):
                gate.validate_plan(p, 'shape')
        fresh = copy.deepcopy(plan)
        fresh.update(stage='validation', selection_receipt=dict(path='prior.json', bytes=10, sha256='a'*64))
        fresh['population']['sha256'] = 'b'*64
        gate.validate_plan(fresh, 'shape')

    def test_auth_source_closure_controls_and_interpreter(self):
        paths = {gate.SELF, gate.SHARED_DRIVER, gate.HARNESS_BASE, gate.BASELINE, gate.TESTS, *gate.PACKAGE}
        contract = dict(inputs=[dict(path=p, sha256='sha256:'+self.ref(self.root/p)['sha256']) for p in paths],
                        controls=[dict(definition=json.dumps(a)) for a in gate.ARMS])
        with patch.object(gate, 'ROOT', self.root), patch.object(gate.driver, 'read_json', return_value=contract), \
             patch.object(gate.driver, 'authenticate', return_value=(contract, self.contract_ref, self.plan)) as auth:
            self.assertEqual(gate.authenticate('synthetic', True)[2], self.plan)
            contract['controls'][2]['definition'] = json.dumps(dict(id='D', mode='P'))
            with self.assertRaisesRegex(ValueError, 'control definitions'):
                gate.authenticate('synthetic', True)
            auth.reset_mock()
            contract['inputs'] = [r for r in contract['inputs'] if r['path'] != gate.BASELINE]
            with self.assertRaisesRegex(ValueError, 'source closure'):
                gate.authenticate('synthetic', True)
            auth.assert_not_called()

    def test_validate_only_and_existing_output_do_not_launch(self):
        with patch.object(gate, 'authenticate', return_value=({}, self.contract_ref, self.plan)), \
             patch.object(gate.driver, 'run_phase') as child, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(gate.main(['--candidate', 'synthetic', '--validate-only']), 0)
        child.assert_not_called()
        (self.output/'keep').write_bytes(b'keep')
        with patch.object(gate, 'ROOT', self.root), patch.object(gate, 'authenticate', return_value=({}, self.contract_ref, self.plan)), \
             patch.object(gate.driver, 'run_phase') as child, self.assertRaisesRegex(ValueError, 'nonempty output'):
            gate.main(['--candidate', self.name])
        child.assert_not_called()

    def test_failure_classification(self):
        base = dict(timeout=False, error=None, argv=['child'], returncode=1)
        for changes, expected in [({}, 'implementation-failure'), ({'timeout':True}, 'budget-exhausted'),
                                   ({'error':'missing'}, 'infrastructure-failure'), ({'returncode':-9}, 'infrastructure-failure')]:
            self.assertEqual(gate.classify_failure(ValueError('failure'), dict(base, **changes), self.plan), expected)


if __name__ == '__main__':
    unittest.main()
