"""Check the actual native recorder against independent synthetic range replay."""
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from tools.causal_field_parent_coder_v1 import Encoder

ROOT=Path(__file__).resolve().parents[1]
PREDICTOR=r'''
#pragma once
#include "gamma-residual-projection.h"
class Predictor {
 public:
  float Predict() { const float p[]={0,0.000015f,0.15f,0.5f,0.85f,0.9999f,1,0.23f};return p[at%8]; }
  void Perceive(unsigned y) {
    history=((history<<1)|y)&255;++at;
    if(at%8==0) { float h[192];for(unsigned j=0;j<192;++j)h[j]=int((history+j/6)%3)-1;gamma_residual::capture(h); }
  }
 private: unsigned at=0,history=0;
};
'''
MAIN=r'''
#include "src/coder/encoder.h"
#include "src/coder/decoder.h"
#include <cassert>
int main(int argc,char**argv) {
 assert(argc==3);Predictor p;
 if(argv[1][0]=='E') {std::ofstream f(argv[2],std::ios::binary);Encoder e(&f,&p);for(unsigned i=0;i<1024;++i)e.Encode((i*13+i/3+5)%2);e.Flush();}
 else {std::ifstream f(argv[2],std::ios::binary);Decoder d(&f,&p);for(unsigned i=0;i<1024;++i)assert(d.Decode()==int((i*13+i/3+5)%2));}
}
'''

class RecorderTests(unittest.TestCase):
    def exercise(self,version):
        with tempfile.TemporaryDirectory() as d:
            work=Path(d);(work/'src/coder').mkdir(parents=True)
            native=ROOT/f'results/fx2_residual_features250k_v{version}/work/native'
            for name in ('encoder.cpp','encoder.h','decoder.cpp','decoder.h'):
                (work/'src/coder'/name).write_bytes((native/'src/coder'/name).read_bytes())
            for name in ('gamma-residual-projection.h','gamma-coder-trace.h'):
                (work/'src'/name).write_bytes((native/'src'/name).read_bytes())
            (work/'src/predictor.h').write_text(PREDICTOR);(work/'main.cpp').write_text(MAIN)
            subprocess.run(['g++','-std=c++17','-O2','main.cpp','src/coder/encoder.cpp','src/coder/decoder.cpp','-o','probe'],cwd=work,check=True,capture_output=True)
            for arm in ('E','D'):
                subprocess.run([str(work/'probe'),arm,'archive'],cwd=work,check=True,capture_output=True,
                    env={**os.environ,'GAMMA_FX2_CODER_TRACE':str(work/(arm+'.coder')),'GAMMA_RESIDUAL_FEATURE_TRACE':str(work/(arm+'.features'))})
            self.assertEqual((work/'E.coder').read_bytes(),(work/'D.coder').read_bytes())
            self.assertEqual((work/'E.features').read_bytes(),(work/'D.features').read_bytes())
            enc=Encoder(max_bits=1024);mismatches=0
            features=list(struct.iter_unpack('<QHBB',(work/'E.features').read_bytes()))
            history=0;expected=0
            for i,row in enumerate(struct.iter_unpack('<7I',(work/'E.coder').read_bytes())):
                _,c,lo,hi,after_lo,after_hi,y=row
                self.assertEqual(y,(i*13+i//3+5)%2)
                self.assertEqual((lo,hi),(enc.low,enc.high))
                self.assertEqual(features[i],(expected,c,i%8|(8 if i>=8 else 0),y))
                enc.encode(y,c)
                mismatches+=(after_lo,after_hi)!=(enc.low,enc.high)
                history=((history<<1)|y)&255
                if i%8==7:
                    expected=sum({-1:2,0:0,1:1}[(history+j)%3-1]<<(2*j) for j in range(32))
            self.assertEqual((work/'archive').read_bytes(),enc.finish())
            return mismatches

    def test_v3_native_recorder_matches_independent_intervals(self):
        self.assertEqual(self.exercise(3),0)

    def test_v2_reproduces_boundary_failure_without_archive_change(self):
        self.assertGreater(self.exercise(2),0)

if __name__=='__main__':unittest.main()
