"""Exercise observers against native transformer and actual arithmetic coders."""
import json
import os
from pathlib import Path
import signal
import struct
import subprocess
import tempfile
import unittest
import zlib

from lib.fx2_value_feedback_native_v1 import materialize, MODEL
from lib.fx2_value_feedback_evidence_v1 import coder_observer_adapter, observe_sources, residual_stream, pack_stream
from tools.fx2_value_feedback250k_v1 import source_members, ZIP
from tests.test_fx2_value_feedback_native_v1 import ROOT, FLAGS, OBJECTS, limits

PROBE = r'''
#include "cpp_infer/src/opt/model_opt.h"
#include <cstdio>
#include <initializer_list>
int main(int argc, char** argv) {
  if(argc != 2) return 2;
  fx2::opt::TransformerOpt m("models/6m-q4-fp32.tfwc2",fx2::opt::AttnKind::KVI8);
  FILE* f=std::fopen(argv[1],"wbx"); if(!f) return 3;
  float prior[205], row[205]; for(auto& v:prior)v=1.0f/205.0f;
  for(int piece: {80,16}) {
    m.begin_article();
    for(int i=0;i<piece;++i){
      m.step((i*31+i/7)%205,prior,row);
      if(std::fwrite(row,sizeof(float),205,f)!=205)return 4;
    }
  }
  return std::fclose(f) ? 5 : 0;
}
'''
CODER_MAIN = r'''
#include "src/coder/encoder.h"
#include "src/coder/decoder.h"
#include <fstream>
#include <string>
int main(int argc,char** argv){
  if(argc!=3)return 2; Predictor p;
  if(std::string(argv[1])=="encode"){
    std::ofstream f(argv[2],std::ios::binary); Encoder e(&f,&p);
    for(int i=0;i<4096;++i)e.Encode(((i*17+i/7)>>(i%7))&1);
    e.Flush();return f.good()?0:3;
  }
  std::ifstream f(argv[2],std::ios::binary);Decoder d(&f,&p);
  for(int i=0;i<4096;++i)if(d.Decode()!=(((i*17+i/7)>>(i%7))&1))return 4;
}
'''
PREDICTOR = b'''#pragma once
class Predictor {unsigned state=0;public:
float Predict(){return float(3+(state%23))/32.0f;}
void Perceive(int bit){state=state*33u+unsigned(bit)+1u;}};
'''


def run(command, cwd, env=None, accepted=0):
    p = subprocess.Popen(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C', **(env or {})},
        start_new_session=True, preexec_fn=limits)
    try: out, err = p.communicate(timeout=180)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGKILL); p.communicate(); raise
    if p.returncode != accepted:
        raise AssertionError(f'{command!r}: {p.returncode}\n{out}\n{err}')
    return out


class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix='gamma-value-evidence-', dir='/run/user/1000')
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.work = Path(cls.tmp.name)
        cls.sources = source_members((ROOT / ZIP).read_bytes())
        cls.adapter = coder_observer_adapter(cls.sources)
        cls.observed = {}
        cls.summary = {}
        header = (ROOT / 'lib/fx2_value_feedback_v1.h').read_bytes()
        for arm in 'PKDS':
            clean = materialize(cls.sources, arm, header)
            observed = observe_sources(clean, arm, cls.adapter,
                (ROOT / 'tools/fx2_coder_trace_v1.hpp').read_bytes(),
                (ROOT / 'lib/fx2_value_feedback_observer_v1.h').read_bytes())
            cls.observed[arm] = observed
            for name, raw in observed.items():
                p = cls.work / arm / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(raw)
        common = cls.work / 'P'
        run(['/usr/bin/make', '-j1', 'CC=/usr/bin/g++', *OBJECTS], common)
        for arm in 'KDS':
            base = cls.work / arm
            (base / 'probe.cpp').write_text(PROBE)
            run(['/usr/bin/g++', *FLAGS, '-I', '.', 'probe.cpp', MODEL,
                 *(str(common / n) for n in OBJECTS), '-o', 'probe'], base)
            trace = base / 'state.bin'
            run([str(base / 'probe'), 'probs.bin'], base, {'GAMMA_VALUE_FEEDBACK_TRACE': str(trace)})
            cls.summary[arm] = residual_stream(trace)
        base = cls.work / 'D'
        run([str(base / 'probe'), 'repeat.bin'], base,
            {'GAMMA_VALUE_FEEDBACK_TRACE': str(base / 'repeat-state.bin')})
        # The delivered source excludes both observers and must give identical probabilities.
        clean = materialize(cls.sources, 'D', header)
        (base / MODEL).write_bytes(clean[MODEL])
        run(['/usr/bin/g++', *FLAGS, '-I', '.', 'probe.cpp', MODEL,
             *(str(common / n) for n in OBJECTS), '-o', 'clean'], base)
        run([str(base / 'clean'), 'clean.bin'], base)
        # Compile actual original/observed coders with a small causal test predictor.
        for role, source in [('original', cls.sources), ('observed', cls.observed['P'])]:
            directory = cls.work / ('coder-' + role)
            for name in ['src/coder/encoder.cpp', 'src/coder/decoder.cpp',
                         'src/coder/encoder.h', 'src/coder/decoder.h']:
                p = directory / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(source[name])
            if role == 'observed':
                (directory / 'src/coder/gamma-coder-trace.h').write_bytes(source['src/coder/gamma-coder-trace.h'])
            (directory / 'src/predictor.h').write_bytes(PREDICTOR)
            (directory / 'main.cpp').write_text(CODER_MAIN)
            run(['/usr/bin/g++', '-O2', '-std=c++17', '-fno-fast-math', 'main.cpp',
                 'src/coder/encoder.cpp', 'src/coder/decoder.cpp', '-o', 'codec'], directory)
            for phase in ('encode', 'decode'):
                env = {'GAMMA_FX2_CODER_TRACE': str(directory / (phase + '.trace'))} if role == 'observed' else None
                run([str(directory / 'codec'), phase, 'archive.bin'], directory, env)
        print('VALUE_OBSERVER_EVIDENCE=' + json.dumps(cls.summary, sort_keys=True), flush=True)

    def test_all_native_residuals_and_resets_repeat(self):
        for arm in 'KDS':
            self.assertEqual(self.summary[arm]['tokens'], 96)
            self.assertEqual(self.summary[arm]['observations'], 96 * 576)
            self.assertEqual(self.summary[arm]['resets'], 2)
            self.assertGreater(self.summary[arm]['nonzero_residuals'], 0)
        d = self.work / 'D'
        self.assertEqual((d / 'state.bin').read_bytes(), (d / 'repeat-state.bin').read_bytes())
        self.assertEqual((d / 'probs.bin').read_bytes(), (d / 'repeat.bin').read_bytes())

    def test_observer_preserves_actual_coder_and_native_probabilities(self):
        d = self.work / 'D'
        self.assertEqual((d / 'probs.bin').read_bytes(), (d / 'clean.bin').read_bytes())
        original, observed = self.work / 'coder-original', self.work / 'coder-observed'
        self.assertEqual((original / 'archive.bin').read_bytes(), (observed / 'archive.bin').read_bytes())
        encode = (observed / 'encode.trace').read_bytes()
        self.assertEqual(len(encode), 4096 * 28)
        self.assertEqual(encode, (observed / 'decode.trace').read_bytes())

    def test_missing_or_reused_trace_path_fails_closed(self):
        d = self.work / 'D'
        run([str(d / 'probe'), 'missing.bin'], d, accepted=125)
        run([str(d / 'probe'), 'exists.bin'], d,
            {'GAMMA_VALUE_FEEDBACK_TRACE': str(d / 'state.bin')}, accepted=125)

    def test_corrupted_truncated_and_false_footer_rejected(self):
        good = (self.work / 'D/state.bin').read_bytes()
        cases = [good[:-1], good[:-16], b'BAD!' + good[4:], good + b'\0' * 4]
        x = bytearray(good); struct.pack_into('<i', x, 8, 32769); cases.append(bytes(x))
        x = bytearray(good); struct.pack_into('<I', x, len(x)-12, 0); cases.append(bytes(x))
        for i, raw in enumerate(cases):
            p = self.work / f'corrupt-{i}'; p.write_bytes(raw)
            with self.subTest(i=i), self.assertRaises(ValueError): residual_stream(p)

    def test_shifted_observer_is_distinct_and_delivery_sources_unchanged(self):
        self.assertNotEqual((self.work / 'D/state.bin').read_bytes(), (self.work / 'S/state.bin').read_bytes())
        for n in ('models/6m-q4-fp32.tfwc2', 'dictionary/english.dic', 'LICENSE'):
            for arm in 'PKDS': self.assertEqual(self.sources[n], self.observed[arm][n])
        bad = dict(self.sources); bad['src/coder/encoder.cpp'] += b'\n'
        with self.assertRaises(ValueError): coder_observer_adapter(bad)

    def test_full_diagnostic_stream_roundtrips_across_packing_boundary(self):
        raw = (bytes(range(256)) * 32768) + b'last-partial-block'
        path = self.work / 'packing-input'; path.write_bytes(raw)
        directory = self.work / 'packed'
        manifest = json.loads(pack_stream(path, directory).read_text())
        self.assertEqual(len(manifest['chunks']), 2)
        restored = b''.join(zlib.decompress((directory / row['file']).read_bytes())
                            for row in manifest['chunks'])
        self.assertEqual(restored, raw)
        self.assertEqual(manifest['original_bytes'], len(raw))


if __name__ == '__main__': unittest.main()
