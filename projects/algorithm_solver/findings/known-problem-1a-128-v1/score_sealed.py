"""Scorer-only recovery after null source metadata; no route replay or changes."""
import json
from pathlib import Path
from algsolve import library_audit as audit
ROOT=audit.LANE_ROOT
OUT=ROOT/'runs/known-problem-1a-128-v1'
REPORT=Path(__file__).parent
write=audit.write

def main():
    seal=json.loads((OUT/'decisions-seal.json').read_text())
    assert audit.sha(OUT/'decisions.json')==seal['sha256']
    contract=json.loads((OUT/'contract.json').read_text())
    for path,sha in contract['source_sha256'].items():
        assert audit.sha(ROOT/path)==sha,path
    _,entries,problems,boundary=audit.inputs()
    assert audit.digest(boundary)==contract['boundary_sha256']
    inv={r['key']:r for r in audit.rows(ROOT/'findings/library-answer-audit-v2/inventory.jsonl')}
    entries={e.key:e for e in entries}
    scored=[]
    for row in json.loads((OUT/'decisions.json').read_text()):
        r=row['result'];e=entries[row['key']]
        score=audit.independent_score(e,r.get('code'),problems,inv[e.key])
        scored.append({'key':e.key,'arm':row['arm'],'decision':r['decision'],'reason':r.get('reason'),
                       'public_examples':r['public_example_count'],'identity_correct':(r.get('source') or {}).get('key')==e.key,
                       'seconds':r['seconds'],'independent':score})
    write(OUT/'scores-recovered.json',scored)
    arms={}
    for arm in ('control','candidate'):
        rows=[r for r in scored if r['arm']==arm]
        arms[arm]={'cases':len(rows),'accepted':sum(r['decision']=='answered' for r in rows),
                   'accepted_and_correct':sum(r['decision']=='answered' and r['identity_correct'] and r['independent']['status']=='passed' for r in rows),
                   'wrong_acceptance':sum(r['decision']=='answered' and (not r['identity_correct'] or r['independent']['status']=='failed') for r in rows),
                   'abstentions':sum(r['decision']!='answered' for r in rows)}
    census=json.loads((OUT/'parser-census.json').read_text())
    manifest=json.loads((ROOT/'findings/known-lookup-release-v2/approved-library.json').read_text())
    summary={'arms':arms,'parser_census':{'eligible':census['eligible'],'changed':len(census['changed']),
        'previously_nonempty_changed':sum(r['previously_nonempty'] for r in census['changed'])},'rows':scored,
        'timing':'contended shared host; no latency promotion','release_promotion':False,'protected_scored':False,
        'model_inference':False,'approval_catalog_unchanged':True,'catalog_counts':manifest['counts'],
        'recovery':'Null result.source crashed original scorer after all38 decisions were sealed. Scorer-only recovery; no replay, retuning or changed decision bytes.',
        'scorer_sha256':audit.sha(Path(__file__))}
    write(OUT/'summary.json',summary)
    for name in ['contract.json','parser-census.json','decisions-seal.json','summary.json']:
        (REPORT/name).write_bytes((OUT/name).read_bytes())
    print(json.dumps(arms,indent=2))
if __name__=='__main__':main()
