#!/usr/bin/env python3
"""Run two independently priced replays of the frozen context-instruction screen."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CID='paid_context_instruction_10m_q0_v1'
def main():
    out=ROOT/'results'/CID
    experiment=json.loads((ROOT/'operations/adaptive/experiments'/(CID+'.json')).read_text())
    for row in experiment['inputs']:
        assert hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest()==row['sha256'].removeprefix('sha256:')
    snapshot=Path(os.environ['GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ROOT'])
    assert (snapshot/'program.py').read_bytes()==(ROOT/'tools/paid_context_instruction_screen_v1.py').read_bytes()
    raw=ROOT/'results/endpoint428_pair_layer0_online_native_trace_10m_v1/wrt_store.bin'
    marker=Path(os.environ['GAMMA_RESOURCE_PHASE_MARKERS'])
    for label in ['first','repeat']:
        with marker.open('a') as f:f.write(json.dumps(dict(phase=label,event='start'))+'\n')
        command=[sys.executable,'-B',str(snapshot/'program.py'),str(raw),str(out/(label+'.json'))]
        run=subprocess.run(command,capture_output=True,timeout=150)
        (out/(label+'.stderr')).write_bytes(run.stderr)
        (out/(label+'.execution.json')).write_text(json.dumps(dict(command=command,returncode=run.returncode))+'\n')
        if run.returncode:raise RuntimeError(run.stderr.decode(errors='replace'))
        with marker.open('a') as f:f.write(json.dumps(dict(phase=label,event='end'))+'\n')
    assert (out/'first.json').read_bytes()==(out/'repeat.json').read_bytes()
    assert (out/'first.model').read_bytes()==(out/'repeat.model').read_bytes()
    x=json.loads((out/'first.json').read_text());x.update(candidate_id=CID,repeatability_pass=True,source_bytes=(snapshot/'program.py').stat().st_size)
    (out/'decision.json').write_text(json.dumps(x,sort_keys=True,indent=2)+'\n')
    print(json.dumps(dict(verdict=x['verdict'],priced_ideal_bytes=x['priced_ideal_bytes'],optimistic_gain_over_counted_parent=x['optimistic_gain_over_counted_parent'])))
if __name__=='__main__':main()
