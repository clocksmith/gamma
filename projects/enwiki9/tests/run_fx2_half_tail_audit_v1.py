#!/usr/bin/env python3
"""Exhaustive probability-domain conversion audit, without native inference."""
import hashlib
import json
import os
from pathlib import Path
import resource
import struct
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'results/fx2_cmix_transformer_static_vocab_fixture50051_q0_v1'


def ref(path):
    data = path.read_bytes()
    return dict(path=str(path.relative_to(ROOT)),bytes=len(data),sha256=hashlib.sha256(data).hexdigest())


def main():
    if len(sys.argv)!=2 or os.sched_getaffinity(0)!={3}:
        raise SystemExit('usage: taskset -c 3 python3 tests/run_fx2_half_tail_audit_v1.py RESULTS_DIRECTORY')
    output=Path(sys.argv[1]).resolve();output.relative_to(ROOT/'results')
    source=BASE/'work/src/predictor.cpp'
    if ref(source)['sha256']!='0b79f43644daee942c9cb6da18fa464f0eb0185b6fc7ffc43cde703808fe537e':
        raise ValueError('native source preimage changed')
    kernel=json.loads((BASE/'kernel.json').read_text())
    probabilities=BASE/'kernel.probabilities.f32le'
    if ref(probabilities)!=kernel['probabilities']:
        raise ValueError('retained kernel probability binding differs')
    inputs=[source,BASE/'kernel.json',probabilities,ROOT/'tools/fx2_transformer_kernel_probe_v1.cpp',
            Path(__file__),ROOT/'operations/provenance/fx2_half_tail_audit_v1_plan.json']
    bindings=[ref(p) for p in inputs]
    output.mkdir(parents=True,exist_ok=False)
    text=source.read_text();start=text.index('float HalfToFloat(uint16_t h)');end=text.index('\n}',start)+2
    original=text[start:end]
    assert original.count('(112 - e)')==1
    exact=original.replace('HalfToFloat','ExactScalar').replace('(112 - e)','(113 - e)')
    cpp='''#include <cstdint>
#include <cstring>
#include <cstdio>
#include <cassert>
#include <immintrin.h>
'''+original+ '\n'+exact+'''
int main() {
  unsigned changed=0, floor_changed=0;
  for(unsigned h=0;h<=0x3c00;++h) {
    float legacy=HalfToFloat(h), corrected=ExactScalar(h), reference=_cvtsh_ss(h);
    assert(std::memcmp(&corrected,&reference,4)==0);
    if(h>0 && h<1024) { assert(legacy*2==corrected); ++changed; }
    else assert(std::memcmp(&legacy,&corrected,4)==0);
    const float p=legacy<1e-6f?1e-6f:legacy;
    const float q=corrected<1e-6f?1e-6f:corrected;
    if(p!=q)++floor_changed;
  }
  std::printf("{\\"probability_patterns\\":15361,\\"scalar_disagreements\\":%u,\\"after_floor_disagreements\\":%u,\\"exact_scalar_matches_f16c\\":true}\\n",changed,floor_changed);
}
'''
    (output/'probe.cpp').write_text(cpp)
    def limits():
        resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912))
        resource.setrlimit(resource.RLIMIT_CPU,(30,30))
        resource.setrlimit(resource.RLIMIT_FSIZE,(33554432,33554432))
    started=time.monotonic();phases=[]
    for name,argv in [('compile',['/usr/bin/g++','-std=c++17','-O2','-march=x86-64-v3','-fno-fast-math',str(output/'probe.cpp'),'-o',str(output/'probe')]),('execute',[str(output/'probe')])]:
        before=resource.getrusage(resource.RUSAGE_CHILDREN);t0=time.monotonic()
        with (output/(name+'.stdout')).open('xb') as out,(output/(name+'.stderr')).open('xb') as err:
            r=subprocess.run(['/usr/bin/timeout','--kill-after=2',str(max(1,int(60-(t0-started)))),*argv],stdout=out,stderr=err,preexec_fn=limits,env={**os.environ,'TMPDIR':str(output)})
        after=resource.getrusage(resource.RUSAGE_CHILDREN)
        phases.append(dict(name=name,argv=argv,returncode=r.returncode,elapsed_seconds=time.monotonic()-t0,cpu_seconds=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,cumulative_child_peak_rss_kib=after.ru_maxrss))
        (output/'phases.json').write_text(json.dumps(phases,indent=2)+'\n')
        if r.returncode:raise ValueError(name+' failed; see retained stderr')
    numeric=json.loads((output/'execute.stdout').read_text())
    data=probabilities.read_bytes();assert len(data)==839680 and data[:419840]==data[419840:]
    values=struct.unpack('<104960f',data[:419840])
    floor=struct.unpack('<f',struct.pack('<f',1e-6))[0]
    columns={str(i):dict(subnormal=0,changed_after_floor=0) for i in range(200,205)}
    changed_rows=0;max_mass_delta=0.0
    for row in range(512):
        mass_delta=0.0;changed=False
        for i in range(200,205):
            h=struct.unpack('<H',struct.pack('<e',values[row*205+i]))[0]
            corrected=struct.unpack('<e',struct.pack('<H',h))[0]
            legacy=corrected/2 if 0<h<1024 else corrected
            columns[str(i)]['subnormal']+=0<h<1024
            p,q=max(floor,legacy),max(floor,corrected)
            columns[str(i)]['changed_after_floor']+=p!=q
            changed|=p!=q;mass_delta+=q-p
        changed_rows+=changed;max_mass_delta=max(max_mass_delta,mass_delta)
    assert bindings==[ref(p) for p in inputs]
    report=dict(schema='gamma.enwiki9.half-tail-audit.v1',status='passed',inputs=bindings,phases=phases,numeric=numeric,
                retained_kernel=dict(unique_synthetic_rows=512,duplicate_repeat_excluded=True,columns=columns,rows_changed_after_floor=changed_rows,maximum_row_mass_increase=max_mass_delta),
                objective_credit_bytes=0,native_model_executed=False,
                scope='Numerical compatibility and synthetic kernel rows only; no corpus event frequency or native archive improvement.',
                next_required='Any output-conversion successor must preserve input half priors and model state, then establish native P/K identity and D inverse/repeat against the unchanged baseline.')
    (output/'receipt.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
