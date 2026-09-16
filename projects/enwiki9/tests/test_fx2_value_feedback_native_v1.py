"""Bounded synthetic native preflight; never a corpus or eligibility gate."""
import hashlib
import io
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import tempfile
import unittest
import zipfile

from lib import fx2_value_feedback_native_v1 as candidate

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'results/fx2_expert_release250k_v3/P-source.zip'
SOURCE_SHA = 'c44d941f95bd8504d63ed6ea5112af3ce15aeffb6874ebddb66596ce083c3cf6'
OBJECTS = ['tf_' + name + '.o' for name in (
    'weights_io', 'weights_io_compressed', 'qmat_dense', 'qmat_sparse',
    'attn', 'kda', 'glue', 'arena_build')]
FLAGS = ['-m64', '-O3', '-std=c++17', '-Wall', '-Wextra', '-fno-math-errno',
         '-fdata-sections', '-ffunction-sections', '-march=x86-64-v3',
         '-mtune=generic', '-mrecip=none']


def limits():
    os.sched_setaffinity(0, {4})
    resource.setrlimit(resource.RLIMIT_AS, (2_000_000_000,) * 2)
    resource.setrlimit(resource.RLIMIT_CPU, (180,) * 2)
    resource.setrlimit(resource.RLIMIT_FSIZE, (64_000_000,) * 2)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def run(command, cwd):
    p = subprocess.Popen(command, cwd=cwd, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, start_new_session=True,
                         preexec_fn=limits,
                         env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C'})
    try:
        out, err = p.communicate(timeout=180)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGKILL)
        p.communicate()
        raise
    if p.returncode:
        raise AssertionError(f'{command!r}: {p.returncode}\n{out}\n{err}')
    return out


class NativeFeedbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data = SOURCE.read_bytes()
        if hashlib.sha256(data).hexdigest() != SOURCE_SHA:
            raise AssertionError('source ZIP identity differs')
        compiler = Path('/usr/bin/g++').resolve()
        profile = json.loads((ROOT / 'operations/provenance/'
                             'fx2_kda_carry_toolchain_20260913.json').read_text())
        binding = next(row for row in profile['toolchain']
                       if Path(row['path']) == compiler)
        if hashlib.sha256(compiler.read_bytes()).hexdigest() != binding['sha256']:
            raise AssertionError('compiler identity differs')
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            cls.original = {name: z.read(name) for name in z.namelist()}
        cls.header = (ROOT / 'lib/fx2_value_feedback_v1.h').read_bytes()
        cls.tmp = tempfile.TemporaryDirectory(prefix='gamma-value-native-', dir='/run/user/1000')
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.work = Path(cls.tmp.name)
        cls.sources = {}
        cls.binary = {}
        cls.outputs = {}
        cls.observations = {}
        for arm in 'PKDS':
            sources = candidate.materialize(cls.original, arm, cls.header)
            cls.sources[arm] = sources
            base = cls.work / arm
            for name, contents in sources.items():
                p = base / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(contents)
            (base / 'probe.cpp').write_bytes(
                (ROOT / 'tests/fx2_value_feedback_native_probe_v1.cpp').read_bytes())
        common = cls.work / 'P'
        run(['/usr/bin/make', '-j1', 'CC=/usr/bin/g++', *OBJECTS], common)
        for arm in 'PKDS':
            base = cls.work / arm
            model = base / candidate.MODEL
            run([str(compiler), *FLAGS, '-DGAMMA_VALUE_FEEDBACK_PROBE', '-c',
                 str(model), '-o', 'model.o'], base)
            binary = base / 'probe'
            run([str(compiler), *FLAGS, '-I', str(base), 'probe.cpp', 'model.o',
                 *(str(common / obj) for obj in OBJECTS), '-o', str(binary)], base)
            cls.binary[arm] = binary
            for label, count in [('full', 1088), ('repeat', 1088), ('prefix', 64)]:
                output = base / (label + '.f32')
                evidence = run([str(binary), 'models/6m-q4-fp32.tfwc2', str(output),
                                str(count), str('PKDS'.index(arm)), '0'], base)
                cls.outputs[arm, label] = output.read_bytes()
                cls.observations[arm, label] = json.loads(evidence)
        # One uninstrumented treatment checks that observation did not alter it.
        base = cls.work / 'D'
        run([str(compiler), *FLAGS, '-c', str(base / candidate.MODEL),
             '-o', 'model-clean.o'], base)
        run([str(compiler), *FLAGS, '-I', str(base), 'probe.cpp', 'model-clean.o',
             *(str(common / obj) for obj in OBJECTS), '-o', 'probe-clean'], base)
        run([str(base / 'probe-clean'), 'models/6m-q4-fp32.tfwc2',
             'clean.f32', '1088', '0', '0'], base)
        cls.clean = (base / 'clean.f32').read_bytes()
        cls.evidence = dict(source_zip_sha256=SOURCE_SHA,
            observations={f'{a}-{label}': row for (a, label), row in cls.observations.items()},
            streams={f'{a}-{label}': dict(bytes=len(value), sha256=hashlib.sha256(value).hexdigest())
                     for (a, label), value in cls.outputs.items()},
            clean_D_sha256=hashlib.sha256(cls.clean).hexdigest(),
            native_steps=sum(r['tokens'] + 64 for r in cls.observations.values()) + 1152,
            corpus_bytes=0, archive_bytes=None, score_credit_bytes=0)
        print('NATIVE_FEEDBACK_EVIDENCE=' + json.dumps(cls.evidence, sort_keys=True), flush=True)

    def test_parent_and_bookkeeping_probabilities_identical(self):
        self.assertEqual(self.outputs['P', 'full'], self.outputs['K', 'full'])

    def test_repeats_and_prefix_causality(self):
        for arm in 'PKDS':
            self.assertEqual(self.outputs[arm, 'full'], self.outputs[arm, 'repeat'])
            self.assertEqual(self.outputs[arm, 'prefix'], self.outputs[arm, 'full'][:64 * 205 * 4])
            self.assertEqual(len(self.outputs[arm, 'full']), 1088 * 205 * 4)

    def test_treatment_and_misaligned_control_change_native_predictions(self):
        self.assertNotEqual(self.outputs['D', 'full'], self.outputs['P', 'full'])
        self.assertNotEqual(self.outputs['D', 'full'], self.outputs['S', 'full'])

    def test_reset_ring_crossing_residual_bounds_and_activation(self):
        for arm in 'KDS':
            row = self.observations[arm, 'full']
            self.assertEqual(row['observations'], 1152 * 576)
            self.assertEqual(row['resets'], 2)
            self.assertGreater(row['nonzero_residuals'], 0)
            self.assertLessEqual(row['maximum_abs_residual'], 32768)

    def test_observer_does_not_change_treatment_predictions(self):
        self.assertEqual(self.outputs['D', 'full'], self.clean)

    def test_source_boundary_and_parent_delivery_identity(self):
        self.assertEqual(self.original, self.sources['P'])
        for arm in 'KDS':
            self.assertEqual(set(self.sources[arm]) - set(self.original), {candidate.HEADER})
            self.assertEqual([p for p in self.original
                              if self.original[p] != self.sources[arm][p]], [candidate.MODEL])

    def test_source_and_kernel_mismatch_rejected(self):
        broken = dict(self.original)
        broken[candidate.MODEL] += b'\n'
        with self.assertRaises(ValueError): candidate.materialize(broken, 'D', self.header)
        with self.assertRaises(ValueError): candidate.materialize(self.original, 'D', b'changed')
        with self.assertRaises(ValueError): candidate.materialize(self.original, 'X', self.header)


if __name__ == '__main__':
    unittest.main()
