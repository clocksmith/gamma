"""Hash-bound incremental vocabulary driver, with resumable bounded CPU slices."""
import argparse,json,os,re,time
from pathlib import Path
from search import Builder, ALPHABET, digest, joint
HERE=Path(__file__).resolve().parent

def family(text):
    if re.search(r'\.(left|right)\b',text):return 'node-children'
    if re.search(r'\.next\b',text):return 'node-next'
    if re.search(r'\]\s*\[|\[0\]\.length',text):return 'nested-index'
    if re.search(r'\b(Map|Set)\b',text):return 'keyed-collection'
    if re.search(r'\.length\b|\bArray\b',text):return 'sequence'
    return 'scalar-other'

def freeze(inputs,prior,output):
    old=json.loads(prior.read_text())
    spec,population,references,proof,adapted=joint.pool_gate(inputs,Path(old['baseline_report']),[Path(r['report']) for r in old['adapted_reports']])
    if population!=old['population'] or references!=old['references'] or proof['report_sha256']!=old['baseline_report_sha256'] or adapted!=old['adapted_reports']:raise ValueError('qualified source pool drift')
    ids=[str(p) for p in old['partition']['dev_fit']]
    rows={};owners={};refs={};families={}
    for pid in ids:
        seen={}
        for row in population[pid]:
            raw=Path(row['path']).read_bytes()
            if joint.b.sha(raw)!=row['sha256']:raise ValueError('source drift')
            key=pid+':'+row['label']
            if row['sha256'] in seen:
                if row['label']==references[pid]:refs[pid]=seen[row['sha256']]
                continue
            seen[row['sha256']]=key;rows[key]=row;owners[key]=pid
            if row['label']==references[pid]:refs[pid]=key;families[pid]=family(raw.decode())
    contract={'schema':'gamma.incremental-family-growth.v1','source_rows':rows,'owners':owners,'references':refs,'families':families,'fit_ids':ids,'prior_contract_sha256':joint.b.sha(prior.read_bytes()),'baseline_report_sha256':proof['report_sha256'],'adapted_reports':adapted,'capacities':[128,256],'local_learned_slots':32,'candidate_rule':'all adjacent exact pieces from every qualified variant, at least2 problem owners; no length cap','merge_rule':'greatest shared literal bytes, then shared entries, then lexical family identifiers','objective':['above96','above32','max(0,10C-S)','S','C','literal_utf8_bytes'],'family_labels':'pre-cost syntactic organization of frozen references, not semantic/correctness authority','code_sha256':{n:joint.b.sha((HERE/n).read_bytes()) for n in ['search.py','run.py','FREEZE.md']},'m1_population':500,'fit_population':300,'protected_access':False,'m1_qualified':False}
    output.mkdir(parents=True,exist_ok=False);joint.b.write(output/'contract.json',contract)
    return {'status':'frozen','families':dict(__import__('collections').Counter(families.values())),'source_variants':len(rows)}

def run(freeze_path,output,capacity,cpu):
    raw=(freeze_path/'contract.json').read_bytes();c=json.loads(raw)
    if c['code_sha256']!={n:joint.b.sha((HERE/n).read_bytes()) for n in c['code_sha256']} or c['capacities']!=[128,256] or c['fit_population']!=300 or c['protected_access'] is not False:raise ValueError('frozen algorithm/scope drift')
    texts={}
    for k,row in c['source_rows'].items():
        content=Path(row['path']).read_bytes()
        if joint.b.sha(content)!=row['sha256']:raise ValueError('qualified source changed')
        texts[k]=content.decode()
    output.mkdir(parents=True,exist_ok=True)
    identity={'contract_sha256':joint.b.sha(raw),'capacity':capacity}
    p=output/'identity.json'
    if p.exists() and json.loads(p.read_text())!=identity:raise ValueError('resume identity mismatch')
    joint.b.write(p,identity)
    ledger=output/'ledger.jsonl';resume=[json.loads(line) for line in ledger.read_text().splitlines()] if ledger.exists() else []
    width=7 if capacity==128 else 8
    def record(event):
        selected={pid:texts[key] for pid,key in event['source_choices'].items()}
        measured,_=joint.compare.measure(selected,ALPHABET+event['learned_literals'],width)
        if measured['selections']!=event['metrics']['selections'] or measured['single_character_bits']//width!=event['metrics']['characters']:raise ValueError('independent cost/decode differs')
        # Cost evidence is separately hash-bound: the core event hash stays canonical.
        proof={k:v for k,v in measured.items() if k not in ('per_problem','entry_problem_support')}
        proof['event_sha256']=event['sha256']
        with (output/'costs.jsonl').open('a') as f:f.write(json.dumps(proof,sort_keys=True)+'\n');f.flush();os.fsync(f.fileno())
        with ledger.open('a') as f:f.write(json.dumps(event,sort_keys=True)+'\n');f.flush();os.fsync(f.fileno())
        joint.b.write(output/'progress.json',{'operation':event['operation'],'events':len(resume)+len(builder.events),'metrics':event['metrics'],'event_sha256':event['sha256'],'status':'running'})
        print(json.dumps({'operation':event['operation'],'entries':event['metrics']['entries'],'programs':event['metrics']['programs'],'selections':event['metrics']['selections']}),flush=True)
    builder=Builder(texts,c['owners'],c['references'],c['families'],capacity=capacity,record=record,resume=resume,cpu_seconds=cpu)
    try:
        state=builder.run();summary,artifacts=joint.compare.measure({p:texts[k] for p,k in state['choices'].items()},ALPHABET+state['learned'],width)
        (output/'dictionary.bin').write_bytes(artifacts['dictionary'])
        joint.b.write(output/'final-state.json',{'learned_literals':state['learned'],'choices':state['choices']})
        for pid,packet in artifacts['packets'].items():(output/(pid+'.packet')).write_bytes(packet)
        result={'status':'completed','contract_sha256':joint.b.sha(raw),'capacity':capacity,'fit_population':300,'m1_population':500,'protected_access':False,'m1_qualified':False,'ledger_head':builder.chain,'measurement':summary}
        joint.b.write(output/'results.json',result);return {'status':'completed','metrics':state['metrics']}
    except TimeoutError as error:
        return {'status':'paused_budget','reason':str(error),'ledger_head':builder.chain,'resume':str(output)}

if __name__=='__main__':
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    f=sub.add_parser('freeze');f.add_argument('--inputs',type=Path,required=True);f.add_argument('--prior',type=Path,required=True)
    r=sub.add_parser('run');r.add_argument('--freeze',type=Path,required=True);r.add_argument('--capacity',type=int,choices=[128,256],required=True);r.add_argument('--cpu-seconds',type=int,default=240)
    for t in (f,r):t.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(json.dumps(freeze(a.inputs,a.prior,a.output) if a.command=='freeze' else run(a.freeze,a.output,a.capacity,a.cpu_seconds)))
