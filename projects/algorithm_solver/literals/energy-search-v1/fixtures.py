"""Small unexecuted text fixtures and source-informed human seeds. No training."""
from pathlib import Path
import json
from harness import ROOT,identity,raw_hash,mine_pieces,VocabularyState,CandidatePiece

SEED_FIXTURE=ROOT/'human-seed-fixture.json'
SEED_FIXTURE_SHA='7c733e95ea3fd4464156076d02c343015eb0ef555c5caaba1a506e30f24d9b2d'

def seed_inventory():
    raw=SEED_FIXTURE.read_bytes()
    assert raw_hash(raw)==SEED_FIXTURE_SHA
    inventory=json.loads(raw)
    assert inventory['qualified_components']==0
    for seed in inventory['seeds']:
        assert raw_hash(seed['text'].encode())==seed['sha256']
        assert seed['receipt_needed'] is True and seed['witnesses']
        for witness in seed['witnesses']:
            assert set(witness)=={'key','source_sha256','qualified'}
            assert witness['qualified'] is False
            assert len(witness['source_sha256'])==64 and all(c in '0123456789abcdef' for c in witness['source_sha256'])
    return inventory

def synthetic_dataset():
    inventory=seed_inventory();helper=inventory['seeds'][-1]['text']
    variants={};contracts={};qualifications={}
    families={'synthetic-train':'train','synthetic-a':'validation','synthetic-b':'validation','synthetic-test':'test'}
    for problem,family,variable in [('fixture-train','synthetic-train','items'),('fixture-a','synthetic-a','values'),('fixture-b','synthetic-b','numbers'),('fixture-test','synthetic-test','inputs')]:
        for alternative,name in [('original',variable),('renamed','elements')]:
            # Mechanism fixture only: no candidate execution or semantic-equivalence label.
            source=helper+f'function {problem.replace("-", "_")}({name}) {{\n  const counts = new Map();\n  for (const value of {name}) {{\n    countIncrement(counts, value);\n  }}\n  return counts.size;\n}}\n'
            key=problem+':'+alternative;cid=problem+':javascript'
            contract={'problem_id':problem,'language':'javascript','output':'synthetic text fixture, no executable qualification','mutation':'fixture declaration only','alias':'fixture declaration only','numeric':'fixture declaration only','complexity':'fixture declaration only','domain':'synthetic strings, not LeetCode input','component_refs':['integer_count_read_increment_pilot_v1']}
            contracts[cid]=contract;csha=identity(contract);sha=raw_hash(source.encode());qid=key+':synthetic'
            variants[key]={'id':key,'problem_id':problem,'family_id':family,'language':'javascript','aliases':[problem], 'source':source,'source_sha256':sha,'contract_id':cid,'contract_sha256':csha,'qualification_id':qid,'implicit_code':False,'helper_spans':[{'start':0,'end':len(helper),'sha256':raw_hash(helper.encode())}],'operand_bits':0,'control_bits':0}
            qualifications[qid]={'source_sha256':sha,'contract_sha256':csha,'status':'passed','gates':{k:True for k in ['output','mutation','alias','numeric','complexity','domain']},'evidence_class':'synthetic_fixture_only','candidate_execution':False,'note':'Eligibility-shaped fixture only, no real qualification evidence.'}
    return {'schema':'gamma.energy-dataset.v1','corpus_id':'synthetic-count-shape-v1','evidence_class':'synthetic_fixture_only','reviewed_manifest':True,'contracts':contracts,'variants':variants,'qualifications':qualifications,'split':{'id':'synthetic-family-split-v1','seed':20261021,'exposed_development':True,'frozen_before_scoring':True,'families':families},'excluded':{'problem_ids':[],'family_ids':[],'source_sha256':[],'aliases':[]}},inventory

def comparison_pool(data,inventory,track,seed_policy,width):
    if seed_policy not in ('mined-only','human-plus-mined','designed-only'):raise ValueError('unknown seed policy')
    keys=[k for k,v in data['variants'].items() if data['split']['families'][v['family_id']]=='validation']
    human=[x['text'] for x in inventory['seeds'] if x['language']=='javascript' and any(x['text'] in data['variants'][k]['source'] for k in keys)] if seed_policy!='mined-only' else []
    if seed_policy=='designed-only':
        pieces={raw_hash(text.encode()):CandidatePiece(raw_hash(text.encode()),text,track,tuple(k for k in keys if text in data['variants'][k]['source'])) for text in human}
    else:
        pieces=mine_pieces(data,keys,track,human)
    # Initial construction is deterministic and independent of later measured costs.
    selected=[p for p,x in pieces.items() if seed_policy=='designed-only' or (len(x.text)==1 if track=='compression' else True)]
    if human:
        selected.extend(raw_hash(x.encode())for x in human if raw_hash(x.encode())in pieces)
    selected=tuple(sorted(set(selected)))
    if len(selected)>2**width:raise ValueError('seed does not fit')
    choices=tuple(sorted((data['variants'][k]['problem_id'],k) for k in keys if k.endswith(':original')))
    return pieces,VocabularyState(selected,choices,width,track)

if __name__=='__main__':
    data,seeds=synthetic_dataset()
    for name,record in [('dataset.synthetic.json',data),('human-seeds.json',seeds)]:
        path=ROOT/name
        with path.open('x')as f:json.dump(record,f,indent=2);f.write('\n')
        print(name,raw_hash(path.read_bytes()))
