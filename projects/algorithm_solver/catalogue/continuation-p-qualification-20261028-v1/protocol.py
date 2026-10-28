"""Fixed original-P Python/new official-JS qualification preparation and runner."""
from __future__ import annotations
import argparse
from dataclasses import asdict
import importlib.util
from pathlib import Path
import urllib.request

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
SUPPORT=ROOT/'projects/algorithm_solver/catalogue/continuation-no-qualification-20261028-v1/protocol.py'
def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
engine=module(SUPPORT,'p_existing_judge_support')
encoded,sha,read_json,write,exact=engine.encoded,engine.sha,engine.read_json,engine.write,engine.exact
IDS=(17,37,65,87,95,99,108,114,116,117)
LANGUAGES=('python','javascript')
REFERENCE=Path('projects/algorithm_solver/catalogue/authored/continuation-p-20261028-v1')
OFFICIAL_JS=Path('projects/algorithm_solver/catalogue/authored/continuation-p-js-official-20261028-v1')
OBSERVERS=Path('projects/algorithm_solver/catalogue/continuation-p-official-observers-20261028-v2')
DIRECTORIES={'python':REFERENCE,'javascript':OFFICIAL_JS}
LIMITS=engine.LIMITS
ARGV=engine.ARGV
MAX_INPUT_BYTES=16*1024**2
POLICY='p-fieldwise-conservative-v1;repeat-small;large-bracket-or-singleton;retain-blocked'
FLAGS=('independent_source_review','source_safety','exact_domain_interface','numeric_contract',
       'mandatory_complexity','effects_contract','independent_references_and_boundaries',
       'language_specific_official_entry','original_node_constructor_and_identity','native_mutation_and_topology')
SCHEMA='gamma.p-official-execution.v1'
DEFINITION_QUERY='query questionData($titleSlug: String!) { question(titleSlug:$titleSlug) { questionId questionFrontendId title titleSlug isPaidOnly content exampleTestcaseList metaData } }'
TEMPLATE_QUERY='query questionData($titleSlug:String!){question(titleSlug:$titleSlug){questionFrontendId title titleSlug isPaidOnly codeSnippets{lang langSlug code}}}'
SCOPE='Finite exposed original Python Solution.method/new JavaScript official-function cases; no old class-only JS, canonical adoption, formal proof or held-out claim.'


def population():
    pop=read_json(HERE/'population.json')
    if pop.get('schema')!='gamma.fixed-p-official-population.v1' or pop.get('ids')!=list(IDS) or pop['source_directories']!={k:str(v)for k,v in DIRECTORIES.items()}:
        raise ValueError('fixed selected P population changed')
    if tuple(r['id']for r in pop['problems'])!=IDS:raise ValueError('definition population changed')
    for lang,d in DIRECTORIES.items():
        for name,pin in pop['source_metadata'][lang].items():
            if name not in ('manifest.json','assignment.public-safe.json')or sha((ROOT/d/name).read_bytes())!=pin:raise ValueError('selected source metadata drift')
    if sha((ROOT/REFERENCE/'pre-source-reference-freeze.json').read_bytes())!=pop['reference_freeze_sha256']:raise ValueError('original reference freeze drift')
    profile=read_json(ROOT/OBSERVERS/'native-bindings.json')
    if sha((ROOT/OBSERVERS/'native-bindings.json').read_bytes())!=pop['profile_sha256'] or profile['source_directories']!={k:str(v)for k,v in DIRECTORIES.items()}:
        raise ValueError('selected language observer profile drift')
    if profile['language_entry_kinds']!={'javascript':'original official function export','python':'original Solution.method'}or profile['solve_fallback']is not False or profile['constructor_injection']is not False:
        raise ValueError('original official route required')
    for name,pin in profile['helper_sha256'].items():
        if name not in ('harness.py','harness.cjs','host_check.py')or sha((ROOT/OBSERVERS/name).read_bytes())!=pin:raise ValueError('official observer helper drift')
    return pop


def inventory(pop):
    result={}
    for lang,d in DIRECTORIES.items():
        for row in read_json(ROOT/d/'manifest.json')['source_inventory']:
            if row['language']!=lang:continue
            pid=row['id'];suffix='py'if lang=='python'else'js'
            if type(pid)is not int or pid not in IDS or (pid,lang)in result or row['path']!=f'{lang}/{pid}.{suffix}':raise ValueError('selected source locator drift')
            semantics=Path(row['semantics_path'])
            if semantics.parent!=Path('semantics')or semantics.suffix!='.json':raise ValueError('semantics locator escaped')
            result[pid,lang]=row
    if set(result)!={(p,l)for p in IDS for l in LANGUAGES}:raise ValueError('missing selected source')
    return result


def live(g,pid,lang,kind):engine.access(g,pid,lang,kind)

def definition_read(args,g,pid,path):
    if pid not in IDS or path!=args.statements/f'{pid}.json':raise ValueError('unassigned definition path')
    for lang in LANGUAGES:live(g,pid,lang,'statement')
    return engine.bounded_regular_read(path,maximum_bytes=4*1024**2)


def validate_definition(raw,spec):
    q=read_question(raw,spec)
    if sha(raw)!=spec['response_sha256']or sha(q['content'].encode())!=spec['content_sha256']or sha(encoded(__import__('json').loads(q['metaData'])))!=spec['api_sha256']:
        raise ValueError('exact original public definition/content/API changed')
    return q


def read_question(raw,spec):
    q=__import__('json').loads(raw)['data']['question']
    if (type(q)is not dict or q.get('questionFrontendId')!=str(spec['id'])or q.get('titleSlug')!=spec['slug']or q.get('title')!=spec['title']or q.get('isPaidOnly')is not False):raise ValueError('official public identity changed')
    return q


def validate_templates(raw,spec):
    q=read_question(raw,spec);pins={}
    for lang,slug in (('python','python3'),('javascript','javascript')):
        snippets=[r for r in q['codeSnippets']if r['langSlug']==slug]
        if len(snippets)!=1 or type(snippets[0]['code'])is not str:raise ValueError('exact language template missing')
        pin=spec['templates'][lang]
        if sha(raw)!=pin['response_sha256']or sha(snippets[0]['code'].encode())!=pin['template_sha256']:raise ValueError('official language-template raw/code changed')
        pins[lang]=dict(pin)
    return pins


def inputs(args,pop,g):
    pins={}
    for spec in pop['problems']:
        pid=spec['id'];raw=definition_read(args,g,pid,args.statements/f'{pid}.json');validate_definition(raw,spec)
        for lang in LANGUAGES:live(g,pid,lang,'statement')
        templates=engine.bounded_regular_read(args.statements/f'{pid}.templates.json',maximum_bytes=4*1024**2)
        pins[str(pid)]={'definition_raw_sha256':sha(raw),'templates_raw_sha256':sha(templates),'language_templates':validate_templates(templates,spec)}
    return pins


def prepare(args):
    pop=population();g=engine.gate_file(args.gate,args.gate_sha256)
    args.statements.mkdir(parents=True,exist_ok=False)
    for spec in pop['problems']:
        for query,suffix,validator in ((DEFINITION_QUERY,'.json',validate_definition),(TEMPLATE_QUERY,'.templates.json',validate_templates)):
            for lang in LANGUAGES:
                live(g,spec['id'],lang,'source');live(g,spec['id'],lang,'statement')
            request=urllib.request.Request('https://leetcode.com/graphql/',data=encoded({'query':query,'variables':{'titleSlug':spec['slug']}}),headers={'Content-Type':'application/json','User-Agent':'Gamma public-domain qualification'})
            with urllib.request.urlopen(request,timeout=25)as response:raw=response.read(4*1024**2+1)
            if len(raw)>4*1024**2:raise ValueError('public response exceeds bound')
            validator(raw,spec)
            with (args.statements/f"{spec['id']}{suffix}").open('xb')as stream:stream.write(raw);stream.flush();engine.os.fsync(stream.fileno())
    return {'public_definitions':len(IDS),'public_template_responses':len(IDS),'programs':len(IDS)*len(LANGUAGES),'candidate_executions':0}


def cases(args,pop,g):
    owner=module(ROOT/REFERENCE/'cases.py','p_frozen_case_owner')
    data=owner.build_cases(args.statements,read_raw=lambda pid,path:definition_read(args,g,pid,path))
    freeze=read_json(ROOT/REFERENCE/'pre-source-reference-freeze.json')
    if tuple(data)!=IDS or sha(encoded(data))!=freeze['case_sha256']or {str(p):len(v)for p,v in data.items()}!=freeze['case_counts']:
        raise ValueError('original 7167 reference cases drift')
    return data


def artifacts(pop,g,inv):
    pins={}
    for d in (HERE,ROOT/OBSERVERS,ROOT/REFERENCE):
        for path in sorted(d.iterdir()):
            if path.is_file()and path.suffix in ('.py','.cjs','.json','.md'):pins[str(path.relative_to(ROOT))]=sha(path.read_bytes())
    for path in (SUPPORT,Path(engine.sandbox.__file__),ROOT/'projects/algorithm_solver/catalogue/boundary_policy.py',ROOT/'projects/algorithm_solver/catalogue/public_batch_adapter.py'):
        pins[str(path.relative_to(ROOT))]=sha(path.read_bytes())
    for (pid,lang),row in inv.items():
        for field,pinfield in (('path','sha256'),('semantics_path','semantics_sha256')):
            live(g,pid,lang,'source');path=ROOT/DIRECTORIES[lang]/row[field];raw=engine.bounded_regular_read(path,maximum_bytes=1024**2)
            if sha(raw)!=row[pinfield]:raise ValueError('selected original source/semantics drift')
            pins[str(path.relative_to(ROOT))]=sha(raw)
    # New JS derivation/assignment/contracts remain exact public provenance.
    for path in sorted((ROOT/OFFICIAL_JS).iterdir()):
        if path.is_file()and path.suffix in ('.json','.md'):pins[str(path.relative_to(ROOT))]=sha(path.read_bytes())
    return pins


def review_binding(pop,pid,lang,row):
    spec=next(r for r in pop['problems']if r['id']==pid)
    return {'source_path':str(DIRECTORIES[lang]/row['path']),'source_sha256':row['sha256'],'semantics_sha256':row['semantics_sha256'],
            'source_manifest_sha256':pop['source_metadata'][lang]['manifest.json'],'reference_sha256':sha((ROOT/REFERENCE/'oracles.py').read_bytes()),
            'case_generator_sha256':sha((ROOT/REFERENCE/'cases.py').read_bytes()),'contracts_sha256':sha((ROOT/REFERENCE/'contracts.json').read_bytes()),
            'definition_content_sha256':spec['content_sha256'],'interface_api_sha256':spec['api_sha256'],
            'official_language_template_sha256':spec['templates'][lang]['template_sha256'],'official_template_response_sha256':spec['templates'][lang]['response_sha256'],
            'observer_profile_sha256':pop['profile_sha256'],'observer_sha256':sha((ROOT/OBSERVERS/('harness.py'if lang=='python'else'harness.cjs')).read_bytes()),
            'host_checker_sha256':sha((ROOT/OBSERVERS/'host_check.py').read_bytes())}


def reviews(path,pop,inv):
    if path is None:rows=[]
    else:
        if sha(path.read_bytes())!=pop['review_sha256']:raise ValueError('exact independently reviewed selected P receipt required')
        rows=read_json(path)['programs']
    supplied={}
    for row in rows:
        key=row.get('problem_id'),row.get('language')
        if type(row.get('problem_id'))is not int or key not in inv or key in supplied:raise ValueError('unknown/duplicate selected review')
        supplied[key]=row
    result={}
    for (pid,lang),source in inv.items():
        row=supplied.get((pid,lang),{});binding=review_binding(pop,pid,lang,source)
        approved=all(exact(row.get(k),v)for k,v in binding.items())and all(row.get(flag)is True for flag in FLAGS)and type(row.get('reviewer'))is str and bool(row['reviewer'].strip())
        result[f'{pid}:{lang}']={'approved':approved,'record':row}
    return result


def packet(pid,rows,indices):return {'schema':'gamma.p-official-wrapper-packet.v1','problem_id':pid,'calls':[{'args':rows[i]['args']}for i in indices]}


def output_bound(pid,row):
    """Conservative fieldwise successful-record bytes, not measured output.

    Node row values fit signed32 and IDs<20000: 1024 bytes per physical node
    covers both before/after identity rows, pointers and normalized tree values.
    Four argument serializations cover before/after plus representation margins;
    256 bytes per forest root covers root IDs and markers; 8192 covers all fixed
    metadata/field names. Forest sharing reduces physical nodes, never increases.
    """
    args=row['args'];base=8192+4*len(encoded(args));nodes=roots=0
    if pid==95:
        n=args[0];catalan=(1,1,2,5,14,42,132,429,1430)[n];nodes=n*catalan;roots=catalan
    elif pid==108:nodes=len(args[0]);roots=1
    elif pid in (99,114,116,117):nodes=sum(v is not None for v in next(iter(args[0].values())));roots=1
    return base+1024*nodes+256*roots+(2*len(encoded(row['expected']))if pid in(17,65,87)else 0)


def batch_plan(pid,rows):
    if not rows:raise ValueError('nonempty prepared cases required')
    def measure(indices,policy):return {'indices':indices,'policy':policy,'input_bytes':len(encoded(packet(pid,rows,indices))),'conservative_output_bound_bytes':sum(output_bound(pid,rows[i])+32 for i in indices)+64}
    def fits(p):return p['input_bytes']<=MAX_INPUT_BYTES and p['conservative_output_bound_bytes']<=LIMITS.max_output_bytes
    probe=min(range(len(rows)),key=lambda i:output_bound(pid,rows[i]));batches=[];blocked=[];small=[]
    def flush():
        if small:batches.append(measure(small+[small[0]],'small-repeat-first'));small.clear()
    for index,row in enumerate(rows):
        if output_bound(pid,row)>1024**2 or len(encoded(row['args']))>256*1024:
            flush();options=[measure([index,index],'large-repeat'),measure([probe,index,probe],'small-large-small'),measure([index],'large-singleton-partial-state')];entry=next((p for p in options if fits(p)),None)
            if entry:batches.append(entry)
            else:blocked.append({'case':index,'status':'blocked_transport','category':row.get('category'),'bounds':options[-1]})
        else:
            proposed=measure(small+[index]+[small[0]if small else index],'small-repeat-first')
            if small and(len(small)>=32 or not fits(proposed)):flush()
            small.append(index)
            if not fits(measure(small+[small[0]],'small-repeat-first')):
                small.clear();one=measure([index],'singleton-partial-state')
                if fits(one):batches.append(one)
                else:blocked.append({'case':index,'status':'blocked_transport','category':row.get('category'),'bounds':one})
    flush();covered={i for p in batches for i in p['indices']}
    if covered|{r['case']for r in blocked}!=set(range(len(rows))):raise ValueError('prepared case omitted')
    return {'batches':batches,'blocked_cases':blocked,'logical_cases':len(rows),'admitted_cases':len(covered)}


def parse(raw,count,language):
    if language not in LANGUAGES:raise ValueError('fixed language required')
    def pairs(items):
        result={}
        for k,v in items:
            if k in result:raise ValueError('duplicate observation key')
            result[k]=v
        return result
    json=__import__('json');rows=[json.loads(line,object_pairs_hook=pairs,parse_constant=lambda value:(_ for _ in()).throw(ValueError(value)))for line in raw.decode('utf8').splitlines()]
    if len(rows)!=count+1 or not exact(rows[-1],{'done':count}):raise ValueError('incomplete native stream')
    fields={'i','native_route','problem_id','method','result','result_type','args_before','args_after','alias_edges','node_identity','node_integrity','board_identity'}
    if language=='javascript':fields=fields|{'entry_kind'}
    for i,row in enumerate(rows[:-1]):
        if type(row)is not dict or type(row.get('i'))is not int or row['i']!=i or set(row)!=({'i','error'}if 'error'in row else fields):raise ValueError('native record/order/entry shape')
        if 'error'not in row and language=='javascript'and row['entry_kind']!='javascript-official-function':raise ValueError('actual official function route required')
    return rows[:-1]


def verdict(pid,lang,rows,indices,metadata,stdout):
    if type(metadata.get('exit_code'))is not int or metadata['exit_code']!=0 or metadata.get('timed_out')is not False or metadata.get('output_limit_exceeded')is not False:return [{'case':i,'reason':'sandbox_process_failure'}for i in indices]
    try:records=parse(stdout,len(indices),lang)
    except(ValueError,TypeError,UnicodeError):return [{'case':i,'reason':'observation_protocol'}for i in indices]
    checker=module(ROOT/OBSERVERS/'host_check.py','p_independent_host_checker');failures=[]
    for i,record in zip(indices,records):
        valid,reason=checker.check_observation(pid,rows[i]['args'],record,lang)
        if not valid:failures.append({'case':i,'reason':reason})
    return failures


def summary(pid,lang,rows,plan,failures,total,review):
    expected=sum(len(p['indices'])for p in plan['batches'])
    complete=total==expected and total>0 and not failures and not plan['blocked_cases']and plan['admitted_cases']==len(rows)
    return {'problem_id':pid,'language':lang,'logical_cases':len(rows),'executed_calls':total,'failures':failures,'transport_blocked':plan['blocked_cases'],'complete_prepared_suite_passed':complete,'mandatory_review_approved':review['approved'],'blocked_review':not review['approved'],'qualified_finite_official_interface':complete and review['approved'],'canonical_admission_changed':False,'scope':SCOPE}


def freeze(args):
    pop=population();g=engine.gate_file(args.gate,args.gate_sha256);runtime=engine.runtime();preflight=args.preflight.read_bytes()
    if sha(preflight)!=args.preflight_sha256 or engine.re.search(rb'\b37 passed\b',preflight)is None:raise ValueError('exact existing37-check passing Linux preflight required')
    definition_pins=inputs(args,pop,g);inv=inventory(pop);pins=artifacts(pop,g,inv);data=cases(args,pop,g)
    value={'schema':SCHEMA,'population_sha256':sha((HERE/'population.json').read_bytes()),'artifact_hashes':pins,'runtime':runtime,'argv':ARGV,'limits':asdict(LIMITS),'max_input_bytes':MAX_INPUT_BYTES,'batch_policy':POLICY,'definitions':definition_pins,'case_sha256':sha(encoded(data)),'case_counts':{str(p):len(v)for p,v in data.items()},'plans':{str(p):batch_plan(p,v)for p,v in data.items()},'reviews':reviews(args.review,pop,inv),'boundary_trusted_hashes':g['trusted_hashes'],'execution_gate_sha256':args.gate_sha256,'preflight_sha256':args.preflight_sha256,'scope':SCOPE,'canonical_admission_changed':False}
    write(args.freeze,value);return {'freeze_sha256':sha(args.freeze.read_bytes()),'problems':len(IDS),'programs':len(IDS)*len(LANGUAGES),'candidate_executions':0,'blocked_cases':sum(len(p['blocked_cases'])for p in value['plans'].values())}


def verified(args,check_runtime):
    raw=args.freeze.read_bytes()
    if sha(raw)!=args.freeze_sha256:raise ValueError('exact freeze hash required')
    value=read_json(args.freeze);pop=population();g=engine.gate_file(args.gate,args.gate_sha256);inv=inventory(pop)
    if value.get('schema')!=SCHEMA or value['population_sha256']!=sha((HERE/'population.json').read_bytes())or not exact(value['argv'],ARGV)or not exact(value['limits'],asdict(LIMITS))or value['max_input_bytes']!=MAX_INPUT_BYTES or value['batch_policy']!=POLICY:raise ValueError('frozen protocol drift')
    if not exact(g['trusted_hashes'],value['boundary_trusted_hashes']):raise ValueError('boundary anchors drift')
    if check_runtime and(args.gate_sha256!=value['execution_gate_sha256']or not exact(engine.runtime(),value['runtime'])):raise ValueError('execution runtime/gate drift')
    if artifacts(pop,g,inv)!=value['artifact_hashes']or inputs(args,pop,g)!=value['definitions']:raise ValueError('frozen source/helper/public evidence drift')
    data=cases(args,pop,g)
    if sha(encoded(data))!=value['case_sha256']or {str(p):batch_plan(p,v)for p,v in data.items()}!=value['plans']:raise ValueError('frozen case/plan drift')
    # Recheck every frozen review binding and false flag without a source execution.
    for (pid,lang),row in inv.items():
        saved=value['reviews'][f'{pid}:{lang}'];record=saved['record'];binding=review_binding(pop,pid,lang,row)
        approved=all(exact(record.get(k),v)for k,v in binding.items())and all(record.get(f)is True for f in FLAGS)and type(record.get('reviewer'))is str and bool(record['reviewer'].strip())
        if saved['approved']is not approved:raise ValueError('frozen review gate drift')
    return raw,value,pop,g,inv,data


def run_or_replay(args,replay=False):
    raw,value,pop,g,inv,data=verified(args,not replay)
    if not replay:
        args.output.mkdir(parents=True,exist_ok=False);write(args.output/'identity.json',{'freeze_sha256':sha(raw),'artifact_hashes':value['artifact_hashes'],'runtime':value['runtime']})
    identity={'freeze_sha256':sha(raw),'artifact_hashes':value['artifact_hashes'],'runtime':value['runtime']}
    if not exact(read_json(args.output/'identity.json'),identity):raise ValueError('run identity drift')
    reports=[];raw_pins={}
    for pid in IDS:
        rows=data[pid];plan=value['plans'][str(pid)]
        for lang in LANGUAGES:
            total=0;failures=[]
            for index,entry in enumerate(plan['batches']if value['reviews'][f'{pid}:{lang}']['approved']else[]):
                indices=entry['indices'];wire=encoded(packet(pid,rows,indices));source=inv[pid,lang];stem=args.output/f'{pid}-{lang}-{index:04d}';start={'problem_id':pid,'language':lang,'indices':indices,'source_sha256':source['sha256'],'input_sha256':sha(wire),'plan':entry}
                if not replay:
                    live(g,pid,lang,'source');source_raw=engine.bounded_regular_read(ROOT/DIRECTORIES[lang]/source['path'],maximum_bytes=1024**2)
                    if sha(source_raw)!=source['sha256']:raise ValueError('source drift before dispatch')
                    filename='harness.py'if lang=='python'else'harness.cjs';observer=(ROOT/OBSERVERS/filename).read_bytes()
                    if sha(observer)!=value['artifact_hashes'][str(OBSERVERS/filename)]or len(wire)!=entry['input_bytes']or len(wire)>MAX_INPUT_BYTES:raise ValueError('dispatch helper/input drift')
                    files={'program.py'if lang=='python'else'program.cjs':source_raw,filename:observer,'inputs.json':wire};write(str(stem)+'.start.json',start)
                    result=engine.sandbox.run(ARGV[lang],files=files,limits=LIMITS);metadata=asdict(result)
                    for name in('stdout','stderr'):
                        stream=metadata.pop(name)
                        with Path(str(stem)+'.'+name).open('xb')as f:f.write(stream);f.flush();engine.os.fsync(f.fileno())
                        metadata[name+'_sha256']=sha(stream);metadata[name+'_bytes']=len(stream)
                    metadata['input_bytes']=len(wire);write(str(stem)+'.result.json',metadata)
                if not exact(read_json(str(stem)+'.start.json'),start):raise ValueError('saved dispatch binding drift')
                metadata=read_json(str(stem)+'.result.json');streams={}
                if not exact(metadata.get('input_bytes'),len(wire)):raise ValueError('saved input count drift')
                for name in('stdout','stderr'):
                    streams[name]=Path(str(stem)+'.'+name).read_bytes()
                    if sha(streams[name])!=metadata.get(name+'_sha256')or not exact(len(streams[name]),metadata.get(name+'_bytes')):raise ValueError('raw stream hash/count drift')
                    raw_pins[stem.name+'.'+name]=sha(streams[name])
                failures.extend(verdict(pid,lang,rows,indices,metadata,streams['stdout']));total+=len(indices)
            result=summary(pid,lang,rows,plan,failures,total,value['reviews'][f'{pid}:{lang}']);path=args.output/f'{pid}-{lang}.summary.json'
            if replay:
                if not exact(read_json(path),result):raise ValueError('program summary differs from raw replay')
            else:write(path,result)
            reports.append(result)
    report={'schema':'gamma.p-official-report.v1','freeze_sha256':sha(raw),'programs':reports,'scope':SCOPE,'canonical_admission_changed':False}
    if replay:
        if not exact(read_json(args.output/'report.json'),report):raise ValueError('aggregate differs from raw replay')
    else:write(args.output/'report.json',report)
    result={'programs':len(reports),'executed_calls':sum(r['executed_calls']for r in reports),'qualified_finite_official_interfaces':sum(r['qualified_finite_official_interface']for r in reports),'candidate_execution_on_replay_host':False if replay else None,'raw_stream_hashes':raw_pins,'canonical_admission_changed':False}
    if replay:write(args.output/'replay.json',{**result,'freeze_sha256':sha(raw),'replay_gate_sha256':args.gate_sha256,'original_execution_gate_sha256':value['execution_gate_sha256']})
    return {k:v for k,v in result.items()if k!='raw_stream_hashes'}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('operation',choices=('prepare','freeze','run','replay'))
    for name in('gate','statements','review','freeze','preflight','output'):parser.add_argument('--'+name,type=Path)
    for name in('gate-sha256','freeze-sha256','preflight-sha256'):parser.add_argument('--'+name)
    args=parser.parse_args();result=prepare(args)if args.operation=='prepare'else freeze(args)if args.operation=='freeze'else run_or_replay(args,args.operation=='replay');print(__import__('json').dumps(result,sort_keys=True))
if __name__=='__main__':main()
