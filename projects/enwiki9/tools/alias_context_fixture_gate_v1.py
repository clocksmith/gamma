#!/usr/bin/env python3
"""Four-arm exact synthetic alias transfer, with independent process replay."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CID = 'alias_context_fixture_q0_v1'


def ref(path):
    return dict(path=str(path.relative_to(ROOT)), bytes=path.stat().st_size,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def main():
    sys.dont_write_bytecode = True
    snapshot = Path(os.environ['GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ROOT'])
    out = ROOT/'results'/CID
    spec = json.loads((ROOT/'operations/planning'/f'{CID}.json').read_text())
    result = {'schema': 'gamma.enwiki9.alias-context-fixture-result.v1',
              'candidate_id': CID, 'population': 'constructed synthetic fixtures only',
              'correctness': True, 'repeatability': True, 'fixtures': {},
              'objective_credit_bytes': 0, 'full_corpus_score_bytes': None}
    marker = os.environ.get('GAMMA_RESOURCE_PHASE_MARKERS')
    for row in spec['fixture_rows']:
        rawpath = ROOT/row['path']; raw = rawpath.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == row['sha256'].removeprefix('sha256:')
        where = out/row['id']; where.mkdir()
        arms = {}; archives = {}; witnesses = {}
        for arm in spec['arms']:
            audits = []
            for phase in ('encode', 'decode', 'repeat'):
                stem = arm+'-'+phase
                target = where/(stem+('.raw' if phase == 'decode' else '.arc'))
                ap = where/(stem+'.audit.json')
                command = [sys.executable, '-B', str(snapshot/'program.py'),
                           'decode' if phase == 'decode' else 'encode', arm,
                           str(where/(arm+'-encode.arc') if phase == 'decode' else rawpath), str(target), str(ap)]
                if marker:
                    with open(marker, 'a') as f: f.write(json.dumps(dict(phase=stem, event='start'))+'\n')
                p = subprocess.run(command, capture_output=True, timeout=30)
                (where/(stem+'.stderr')).write_bytes(p.stderr)
                (where/(stem+'.execution.json')).write_text(json.dumps(dict(command=command, returncode=p.returncode))+'\n')
                if p.returncode: raise RuntimeError(p.stderr.decode(errors='replace'))
                if marker:
                    with open(marker, 'a') as f: f.write(json.dumps(dict(phase=stem, event='end'))+'\n')
                audits.append(json.loads(ap.read_text()))
            archive=(where/(arm+'-encode.arc')).read_bytes()
            assert (where/(arm+'-decode.raw')).read_bytes()==raw
            assert (where/(arm+'-repeat.arc')).read_bytes()==archive
            assert audits[0]==audits[1]==audits[2]
            assert audits[0]['boundary_count']==len(raw)
            archives[arm]=archive;witnesses[arm]=audits[0]
            arms[arm]=dict(archive=ref(where/(arm+'-encode.arc')), restored=ref(where/(arm+'-decode.raw')),
                           repeat=ref(where/(arm+'-repeat.arc')), archive_bytes=len(archive),
                           exact_inverse=True, repeat_byte_identity=True, byte_boundary_state_identity=True)
        assert archives['P']==archives['K']
        assert all(witnesses['P'][key]==witnesses['K'][key] for key in ('probabilities','boundaries','boundary_count'))
        pstate=dict(witnesses['P']['final_state']);kstate=dict(witnesses['K']['final_state'])
        pstate.pop('aliases');kstate.pop('aliases');assert pstate==kstate
        if row['id'] in ('binary', 'no_definition'):
            assert len(set(archives.values()))==1
        result['fixtures'][row['id']]=dict(input=ref(rawpath),arms=arms,
            g_P=len(archives['P'])-len(archives['D']),g_S=len(archives['S'])-len(archives['D']))
    result.update({k:result['fixtures']['transfer'][k] for k in ('g_P','g_S')})
    result['source_bytes']=sum((snapshot/p).stat().st_size for p in ('program.py','fixture_coder.py'))
    result['source_cost_scope']='Both Python files only; interpreter/dependency/package accounting incomplete.'
    result['verdict']='Synthetic transfer supported' if result['g_P']>0 and result['g_S']>0 else 'Synthetic transfer unconfirmed'
    (out/'decision.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    (out/'artifacts.json').write_text(json.dumps([ref(p) for p in sorted(out.rglob('*')) if p.is_file()],indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('verdict','g_P','g_S','source_bytes')}))


if __name__=='__main__':main()
