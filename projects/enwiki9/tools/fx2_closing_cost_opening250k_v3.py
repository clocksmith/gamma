#!/usr/bin/env python3
"""Frozen closing-name opportunity audit; no native compression rerun."""
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from lib.fx2_native_gate_v1 import NativeGate as BaseGate, require, sha
from lib.fx2_closing_cost_v1 import analyze, trace_rows
from tools.wrt_exact import parse_store_bytes, read_dictionary_words

PROFILE='operations/provenance/public_fx2_gcc15_toolchain_20260909.json'


class NativeGate(BaseGate):
    def verify(self):
        # Explicit runtime adapter; retain every original guard and file check.
        self.toolchain=json.loads(self.buffers[PROFILE])
        super().verify()


ID='fx2_closing_cost_opening250k_v3'
PLAN='operations/provenance/'+ID+'_plan.json'
CAPS=dict(cpus=[2],memory_bytes=536870912,swap_bytes=0,scratch_bytes=67108864,wall_seconds=180)


def run(g):
    plan=json.loads(g.buffers[PLAN])
    g.retain_sources()
    body_store=g.buffers[plan['stored']]
    dictionary=ROOT/plan['dictionary']
    parsed=parse_store_bytes(body_store,read_dictionary_words(dictionary))
    raw=g.buffers[plan['raw']]
    require(parsed.decoded==raw and len(raw)==250000,'raw inverse differs')
    body=parsed.stream[5:]
    require(len(body)==151210 and body==body_store[10:],'modeled coordinates differ')
    path=g.work/'modeled.bin';path.write_bytes(body)
    binary=g.work/'scanner';g.copy(plan['scanner'],binary);binary.chmod(0o555)
    g.binaries[str(binary)]=sha(binary)
    for name in ('scan','repeat'):
        g.run(name,[str(binary),str(path),str(g.work/(name+'.bin'))],60)
    left=(g.work/'scan.bin').read_bytes();right=(g.work/'repeat.bin').read_bytes()
    require(left==right,'first divergent scanner byte: '+str(next((i for i,(a,b) in enumerate(zip(left,right)) if a!=b),min(len(left),len(right)))))
    donors=trace_rows(left,len(body))
    report=analyze(body,g.buffers[plan['parent_trace']],donors)
    arms=report['arms'];require(arms['K']['changed_probabilities']==0,'bookkeeping differs')
    floor=plan['minimum_ideal_headroom_bits']
    headroom=report['perfect_probability_ideal_ceiling_bits']>floor
    control_margin=arms['D']['ideal_bits_saved']-max(arms['R']['ideal_bits_saved'],arms['S']['ideal_bits_saved'])
    positive=arms['D']['ideal_bits_saved']>0 and control_margin>0
    report.update(schema='gamma.enwiki9.closing-opportunity-terminal.v1',status='passed',
                  candidate_id=ID,experiment=g.reference,plan=g.artifact(ROOT/PLAN),
                  raw_bytes=len(raw),exact_wrt_inverse=True,scanner_repeat_equal=True,
                  donor_trace=g.artifact(g.work/'scan.bin'),donor_repeat=g.artifact(g.work/'repeat.bin'),
                  minimum_ideal_headroom_bits=floor,headroom_pass=headroom,
                  control_margin_ideal_bits=control_margin,controlled_positive=positive,
                  scientific_verdict='eligible_for_separate_codec_planning' if headroom and positive else 'stop_fixed_development_realization',
                  gate_purpose='opportunity-cost diagnostic; not an archive or standalone decoder',
                  source_component_bytes=len(g.buffers['lib/fx2_closing_replay_v1.hpp']),
                  supplied_parent_trace_bytes=len(g.buffers[plan['parent_trace']]),
                  supplied_dictionary_bytes=len(g.buffers[plan['dictionary']]),
                  native_compression_runs=0,larger_gate_authorized=False,
                  limitations=['Parent probability trace and dictionary are supplied diagnostic dependencies, not free decoder inputs',
                               'The32768-bit floor is an integration-budget decision, not a lower bound on package size',
                               'The ceiling keeps this opportunity set and parent fixed and grants perfect predictions even on incorrect donors',
                               'No finite archive bound, cold-to-warm transfer or full-corpus conclusion follows',
                               'Intermediate state hashes are divergence diagnostics; complete mutable state is serialized at terminal'],
                  commands=g.commands)
    return report


def main():
    validate=sys.argv[1:]==['--validate']
    require(not sys.argv[1:] or validate,'unsupported arguments')
    g=NativeGate(ROOT,ID,CAPS,validate_only=validate)
    if validate:
        print(json.dumps(dict(status='preflight_passed',inputs=len(g.inputs))));return 0
    try:
        report=run(g);g.verify();g.closure()
    except Exception as e:
        report=dict(schema='gamma.enwiki9.closing-opportunity-terminal.v1',status='failed',
                    candidate_id=ID,error=str(e),failure_class=getattr(e,'category','evidence_or_implementation_failure'),
                    commands=g.commands,objective_credit_bytes=0,larger_gate_authorized=False)
    files=[g.artifact(p) for p in sorted(g.result.rglob('*')) if p.is_file()]
    g.write('artifacts.json',dict(files=files,errors=[]))
    report['artifact_manifest']=g.artifact(g.result/'artifacts.json')
    g.write('stage-decision.json',report)
    print(json.dumps({k:report[k] for k in ('status','scientific_verdict','active_bytes','perfect_probability_ideal_ceiling_bits') if k in report}))
    return 0 if report['status']=='passed' else 1


if __name__=='__main__':raise SystemExit(main())
