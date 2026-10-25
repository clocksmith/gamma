"""Resumable source-as-data Python vocabulary growth; never candidate execution."""
import argparse,importlib.util,json,os
from pathlib import Path
from search import Builder,ALPHABET,digest,joint
import prepare
HERE=Path(__file__).resolve().parent;LIT=HERE.parent
s=importlib.util.spec_from_file_location('python_trie_accelerator',LIT/'incremental-merge-v4/accelerator.py');accelerator=importlib.util.module_from_spec(s);s.loader.exec_module(accelerator)

def run(frozen,output,capacity,cpu):
    raw=(frozen/'contract.json').read_bytes();c=json.loads(raw)
    if c.get('schema')!='gamma.python.systematic-literals.v1' or c.get('language')!='python' or c.get('code_sha256')!=prepare.pins() or c.get('fixed_fit_population')!=300 or c.get('m1_population')!=500 or c.get('protected_access') is not False or c.get('validation_texts_loaded') is not False or capacity not in (128,256):raise ValueError('Python freeze identity/scope drift')
    if cpu!=c.get('cpu_seconds_per_slice'):raise ValueError('CPU slice differs from frozen matched budget')
    if output.resolve().is_relative_to(HERE.parents[3]):raise ValueError('private ledger outside repo required')
    texts={}
    for key,row in c['source_rows'].items():
        source=Path(row['path']).read_bytes()
        if joint.b.sha(source)!=row['sha256'] or len(source)!=row['bytes']:raise ValueError('qualified Python source changed')
        texts[key]=source.decode()
    if len(c['references'])!=c['fit_population']:raise ValueError('source denominator mismatch')
    output.mkdir(parents=True,exist_ok=True);identity={'contract_sha256':joint.b.sha(raw),'capacity':capacity,'language':'python'}
    ip=output/'identity.json'
    if ip.exists() and json.loads(ip.read_text())!=identity:raise ValueError('resume identity drift')
    joint.b.write(ip,identity);ledger=output/'ledger.jsonl';resume=[json.loads(line) for line in ledger.read_text().splitlines()] if ledger.exists() else []
    width=7 if capacity==128 else 8
    def record(event):
        summary,_=joint.compare.measure({pid:texts[key] for pid,key in event['source_choices'].items()},ALPHABET+event['learned_literals'],width)
        if summary['selections']!=event['metrics']['selections'] or summary['single_character_bits']//width!=event['metrics']['characters']:raise ValueError('independent segmentation/decode mismatch')
        cost={k:v for k,v in summary.items() if k not in ('per_problem','entry_problem_support')};cost['event_sha256']=event['sha256']
        with (output/'costs.jsonl').open('a') as f:f.write(json.dumps(cost,sort_keys=True)+'\n');f.flush();os.fsync(f.fileno())
        with ledger.open('a') as f:f.write(json.dumps(event,sort_keys=True)+'\n');f.flush();os.fsync(f.fileno())
        joint.b.write(output/'progress.json',{'status':'running','language':'python','operation':event['operation'],'event_sha256':event['sha256'],'metrics':event['metrics'],'fixed_fit_population':300,'covered_fit_population':c['fit_population'],'m1_population':500,'m1_qualified':False})
        print(json.dumps({'operation':event['operation'],'metrics':event['metrics']}),flush=True)
    accelerator.configure(c['kernel_binary_sha256'],Path(c['kernel_path']));joint.compact.Graph=accelerator.TrieGraph
    builder=Builder(texts,c['owners'],c['references'],c['families'],capacity=capacity,record=record,resume=resume,cpu_seconds=cpu)
    try:
        # Once consolidation starts, never rerun/reinitialize family vocabularies.
        key=('consolidation',tuple(sorted(c['references'])))
        if key not in builder.resumed:
            state=builder.family_growth();builder.initial=state['learned']
        state=builder.run()
        summary,artifacts=joint.compare.measure({pid:texts[key] for pid,key in state['choices'].items()},ALPHABET+state['learned'],width)
        if prepare.pins()!=c['code_sha256']:raise ValueError('code changed during fitting')
        (output/'dictionary.bin').write_bytes(artifacts['dictionary'])
        for pid,packet in artifacts['packets'].items():(output/(pid+'.packet')).write_bytes(packet)
        joint.b.write(output/'final-state.json',{'choices':state['choices'],'learned_literals':state['learned']})
        result={'status':'completed','language':'python','contract_sha256':joint.b.sha(raw),'capacity':capacity,'fit_population':c['fit_population'],'fixed_fit_population':300,'m1_population':500,'m1_qualified':False,'protected_access':False,'ledger_head':builder.chain,'measurement':summary}
        joint.b.write(output/'results.json',result);return result
    except TimeoutError as error:
        if prepare.pins()!=c['code_sha256']:raise ValueError('code changed during fitting')
        result={'status':'paused_budget','language':'python','contract_sha256':joint.b.sha(raw),'ledger_head':builder.chain,'reason':str(error),'m1_qualified':False};joint.b.write(output/'slice.json',result);return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--freeze',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--capacity',type=int,choices=[128,256],required=True);p.add_argument('--cpu-seconds',type=int,default=240);a=p.parse_args();r=run(a.freeze,a.output,a.capacity,a.cpu_seconds);print(json.dumps({k:r[k] for k in ('status','language','m1_qualified')}))
