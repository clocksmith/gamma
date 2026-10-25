"""Hash-bound incremental vocabulary driver, with resumable bounded CPU slices."""
import argparse,json,os,re,time
from pathlib import Path
from search import Builder, ALPHABET, digest, joint
from accelerator import configure, TrieGraph as FastGraph
HERE=Path(__file__).resolve().parent

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
    configure(c['kernel_binary_sha256'],Path(c['kernel_path']))
    joint.compact.Graph=FastGraph
    builder=Builder(texts,c['owners'],c['references'],c['families'],capacity=capacity,record=record,resume=resume,cpu_seconds=cpu,initial=c['initial_learned'],audited_helpers=c['audited_helpers'])
    if not resume and c.get('initial_frontier'):
        builder.frontiers[tuple(sorted(c['references']))]=c['initial_frontier']
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
    p=argparse.ArgumentParser();p.add_argument('--freeze',type=Path,required=True);p.add_argument('--capacity',type=int,choices=[128,256],required=True);p.add_argument('--cpu-seconds',type=int,default=240);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(json.dumps(run(a.freeze,a.output,a.capacity,a.cpu_seconds)))
