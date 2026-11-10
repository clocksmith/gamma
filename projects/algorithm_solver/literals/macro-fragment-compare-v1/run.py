"""Fit on the existing development partition; seal before validation source opens."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import resource
import statistics
import sys
import time

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT))
from projects.algorithm_solver.catalogue.known_spec_service import KnownSpecService
import codec
import shapes
import select_literals


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
FSP=module('matched_fragment_spelling',HERE.parent/'fragment-spelling-v1/codec.py')
def load_transform():
    path=HERE.parent/'python-compact-v1/transform.py'
    if not path.is_file():
        raise FileNotFoundError('Compact Python transformer is not provisioned: '+str(path)+
            '. Use --exact-only for the qualified exact-source comparison; '
            'this omits, rather than reproduces, the historical compact diagnostic.')
    return module('matched_python_compact',path)

def sha(raw):return hashlib.sha256(raw).hexdigest()
def packed(x):return (json.dumps(x,sort_keys=True,indent=2)+'\n').encode()
def write(p,x):p.write_bytes(packed(x))
def table_json(table):return [[part.decode() for part in row] for row in table]
def metrics(values):
    if not values:return None
    a=sorted(values);return {'n':len(a),'mean':statistics.mean(a),'p50':statistics.median(a),'p95':a[math.ceil(.95*len(a))-1],'worst':a[-1],'total':sum(a)}


def materialize(service,ids,language,directory):
    sources={};rows=[]
    for pid in ids:
        key=str(pid);v=service.request('leetcode:'+key,language=language,include_source=True)
        artifact=v.get('artifact',{});impl=v.get('consumer_selection',{}).get('implementation',{})
        if artifact.get('status')!='materialized':
            rows.append({'id':pid,'status':'unavailable','reason':v.get('reason',v.get('status'))});continue
        text=artifact['source_utf8'];raw=text.encode()
        if sha(raw)!=impl['source_sha256'] or impl['status']!='qualified':raise ValueError('Source qualification binding')
        if len(raw)>codec.MAX_BYTES:rows.append({'id':pid,'status':'source-limit'});continue
        sources[key]=text; (directory/(key+'.source')).write_bytes(raw)
        rows.append({'id':pid,'status':'available','source_sha256':sha(raw),'receipt_sha256':impl['receipt_sha256'],'runtime_sha256':impl['runtime_sha256'],'tests_sha256':impl['tests_sha256'],'contract_scope':impl['contract_scope'],'caveats':impl['caveats']})
    return sources,rows


def evaluate(sources,table,width,occ,protocol,output=None):
    rows=[];uses=Counter()
    if protocol=='fragment':
        dictionary=[p[0].decode() for p in table]
        fragment_encoder=FSP.FragmentEncoder(dictionary,width)
    for pid,source in sources.items():
        if protocol=='fragment':
            p=fragment_encoder.encode(source);binary=FSP.packet_bytes(p)
            if FSP.decode_packet(binary,dictionary,width)!=source:raise ValueError('FSP roundtrip')
            bits=p.bits;runs=p.mode_switch_bits//(width+1)
            stats={'primary_selections':p.fragment_selections+runs,'spelling_payload_bits':p.spelling_bits,
                   'transition_bits':runs,'concat_count_bits':0,'count_words':0,'macro_calls':0,'spelled_bytes':p.spelling_bytes}
            assert len(bits)==stats['primary_selections']*width+p.spelling_bits+runs
        else:
            enc=codec.Encoder(source.encode(),table,width,occ.get(pid,()))
            bits,_=enc.encode();binary=codec.packet(bits,width)
            decoded,stats=codec.unpack(binary,table,width)
            if decoded!=source.encode():raise ValueError('Macro roundtrip')
            uses.update({int(k):v for k,v in stats.pop('entry_uses').items()})
        row={'id':int(pid),'source_sha256':sha(source.encode()),'payload_bits':len(bits),'payload_word_equivalents':len(bits)/width,
             'packet_bits':len(binary)*8,'packet_word_equivalents':len(binary)*8/width,'framing_bits':72,
             'padding_bits':(-len(bits))%8,'packet_sha256':sha(binary),**stats}
        rows.append(row)
        if output:(output/(str(pid)+'.bin')).write_bytes(binary)
    summary={key:metrics([r[key] for r in rows]) for key in ['payload_bits','payload_word_equivalents','packet_word_equivalents','primary_selections','count_words','spelling_payload_bits','transition_bits','concat_count_bits','spelled_bytes','macro_calls']}
    summary.update({'represented':len(rows),'without_spelling':sum(r['spelled_bytes']==0 for r in rows),'source_bytes':sum(len(s.encode()) for s in sources.values()),'dictionary_entries':len(table),
                    'dictionary_storage_bytes':len(packed(table_json(table))),'dictionary_sha256':sha(packed(table_json(table)))})
    return {'summary':summary,'rows':rows},uses


def trial_score(sources,table,width,occ):
    total=0;uses=Counter()
    for pid,source in sources.items():
        enc=codec.Encoder(source.encode(),table,width,occ.get(pid,()))
        bits,seq=enc.encode();total+=(9+(len(bits)+7)//8)*8
        def walk(token):
            if token[0] in ('entry','macro'):uses[token[1]-2]+=1
            if token[0]=='macro':
                for t in token[2]:walk(t)
            if token[0]=='concat':
                for t in token[1]:walk(t)
        for t in seq:walk(t)
    return total,uses



def train(fit,language,folder,original_banned=()):
    meta,parseerrors=shapes.shapes(fit,language.split("-")[0])
    literals,macros,occ,banned,support=shapes.mine(fit,meta,original_banned)
    print(language,'fit',len(fit),'literal candidates',len(literals),'macro candidates',len(macros),flush=True)
    if len(literals)<255:raise ValueError('Insufficient reusable fragments for matched width')
    trained={}; fitreports={};traces={}
    for width in [6,7,8]:
        k=1<<width;ranked=literals[:k-1]
        greedy=select_literals.select(fit,meta,literals,width,k-1)
        ranked_score=select_literals.packet_score(fit,ranked,width);greedy_score=select_literals.packet_score(fit,greedy,width)
        selected=greedy if greedy_score<ranked_score else ranked
        literal=[(x,) for x in selected];control=literal[:k-2]
        print(language,width,'literal fit packet bits',ranked_score,greedy_score,flush=True)
        mixed=list(control);score,uses=trial_score(fit,mixed,width,occ);trace=[]
        for index,macro in enumerate(macros[:24]):
            choices=[i for i,p in enumerate(mixed) if len(p)==1]
            remove=min(choices,key=lambda i:(uses[i],-i));candidate=list(mixed);candidate[remove]=macro
            value,newuses=trial_score(fit,candidate,width,occ);accepted=value<score
            trace.append({'trial':index,'macro_sha256':sha(packed([x.decode() for x in macro])),'arity':len(macro)-1,'support':support[macro],'fit_bits_before':score,'fit_bits_candidate':value,'accepted':accepted})
            if accepted:mixed,score,uses=candidate,value,newuses
            print(language,width,'trial',index+1,'accepted' if accepted else 'rejected',value,flush=True)
        trained[width]={'fragment':literal,'prefix_literal_control':control,'mixed':mixed};traces[width]={"macro_trials":trace,"literal_frequency_packet_bits":ranked_score,"literal_overlap_packet_bits":greedy_score,"selected_literal_method":"overlap" if greedy_score<ranked_score else "frequency"}
        for name,table in trained[width].items():
            out=folder/f'fit-{width}-{name}';out.mkdir();fitreports[f'{width}-{name}'],_=evaluate(fit,table,width,occ,'fragment' if name=='fragment' else 'prefix',out)
            if name=='fragment' and sum(r['packet_bits'] for r in fitreports[f'{width}-{name}']['rows'])!=min(ranked_score,greedy_score):raise ValueError('Literal score oracle mismatch')
            if name=='mixed' and sum(r['packet_bits'] for r in fitreports[f'{width}-{name}']['rows'])!=score:raise ValueError('Accepted fit score mismatch')
    return trained,fitreports,traces,banned,{"literal_candidates":len(literals),"macro_candidates":len(macros),"parse_errors":parseerrors}

def main():
    p=argparse.ArgumentParser();p.add_argument('--service',type=Path,required=True);p.add_argument('--service-sha256',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--report',type=Path,required=True)
    p.add_argument('--exact-only',action='store_true',help='Run exact-source arms without the separately unqualified compact-Python diagnostic')
    p.add_argument('--prior-attempt',type=Path,help='Optional retained comparison report, for audit linkage only');a=p.parse_args()
    transform=None if a.exact_only else load_transform()
    if a.output.resolve().is_relative_to(ROOT):raise ValueError('Private output must be outside repository')
    a.output.mkdir(parents=True,exist_ok=False)
    service=KnownSpecService.from_config(a.service.resolve(),a.service_sha256)
    partition_path=HERE.parent/'cost-decomposition-v1/contract.json';partition=json.loads(partition_path.read_bytes())['partition']
    fitids=partition['dev_fit'];validids=partition['dev_val']
    assert len(fitids)==300 and len(validids)==100 and not set(fitids)&set(validids)
    pins={p.name:sha(p.read_bytes()) for p in HERE.iterdir() if p.suffix in ('.py','.cjs','.md')}
    pins['fragment-spelling-v1/codec.py']=sha((HERE.parent/'fragment-spelling-v1/codec.py').read_bytes())
    if transform is not None:
        pins['python-compact-v1/transform.py']=sha((HERE.parent/'python-compact-v1/transform.py').read_bytes())
    contract={'service_sha256':a.service_sha256,'partition_sha256':sha(partition_path.read_bytes()),'code_pins':pins,'widths':[6,7,8],
              'fit_ids':fitids,'validation_ids':validids,'source_execution':False,'source_publication':False,'validation_fit':False,'macro_trials':24,
              'compact_diagnostic':'omitted_by_request' if a.exact_only else 'included'}
    write(a.output/'run-contract.json',contract)
    result={'schema':'gamma.macro-fragment-development-comparison.v1','contract_sha256':sha(packed(contract)),'contract':contract,'languages':{},'development_checks':{'native_execution':False,'fresh_native_qualification':False,'prerequisite_receipt':'not_recorded_by_runner'},'limits':['Exposed development comparison, not autonomous solving or unseen generalization.','No candidate execution occurs in this representation runner; exact byte reconstruction reuses historical source qualification only.','Heuristic vocabulary selection; no optimality or novelty claim.','Python compact diagnostics are static only and do not increase qualified coverage.']}
    start=time.monotonic()
    for language in ['javascript','python']:
        folder=a.output/language;folder.mkdir();(folder/'fit').mkdir();(folder/'validation').mkdir()
        print(language,'opening fit sources',flush=True)
        fit,membership=materialize(service,fitids,language,folder/'fit')
        trained,fitreports,traces,banned,mining=train(fit,language,folder)
        seal={str(w):{name:table_json(t) for name,t in arms.items()} for w,arms in trained.items()}
        write(folder/'sealed-tables.json',seal);sealhash=sha(packed(seal));print(language,'tables sealed',sealhash,flush=True)
        valid,validmembership=materialize(service,validids,language,folder/'validation');vm,verrors=shapes.shapes(valid,language)
        vocc={pid:shapes.occurrences(s.encode(),vm.get(pid,{'nodes':[]}),banned) for pid,s in valid.items()}
        reports={}
        for width,arms in trained.items():
            for name,table in arms.items():
                out=folder/f'validation-{width}-{name}';out.mkdir();reports[f'{width}-{name}'],_=evaluate(valid,table,width,vocc,'fragment' if name=='fragment' else 'prefix',out)
                reports[f'{width}-{name}']['summary']['population']=100
        data={'fit_membership':membership,'validation_membership':validmembership,'fit_population':300,'validation_population':100,
              'fit_parse_errors':mining['parse_errors'],'validation_parse_errors':verrors,'literal_candidates':mining['literal_candidates'],'macro_candidates':mining['macro_candidates'],'seal_sha256':sealhash,'trials':traces,'fit':fitreports,'validation':reports}
        if language=='python' and transform is not None:
            def compact_sources(sources):
                compact={};rows=[]
                for pid,source in sources.items():
                    try:
                        transformed,proof=transform.transform(source);compact[pid]=transformed
                        rows.append({'id':int(pid),'status':'transformed','source_sha256':sha(source.encode()),'candidate_sha256':sha(transformed.encode()),'proof':proof})
                    except (transform.Unsupported,SyntaxError,ValueError) as error:
                        compact[pid]=source;rows.append({'id':int(pid),'status':'original-fallback','reason':str(error)})
                return compact,rows
            compact,transformrows=compact_sources(fit)
            cf=folder/'compact-static';cf.mkdir()
            ct,cr,cx,cb,cm=train(compact,'python-compact',cf,banned)
            cs={str(w):{name:table_json(t) for name,t in arms.items()} for w,arms in ct.items()}
            write(cf/'sealed-tables.json',cs)
            compact_valid,valid_transformrows=compact_sources(valid)
            cvm,cve=shapes.shapes(compact_valid,'python')
            cvo={pid:shapes.occurrences(source.encode(),cvm.get(pid,{'nodes':[]}),cb) for pid,source in compact_valid.items()}
            cv={}
            for w,arms in ct.items():
                for name,table in arms.items():
                    target=cf/f'validation-{w}-{name}';target.mkdir()
                    cv[f'{w}-{name}'],_=evaluate(compact_valid,table,w,cvo,'fragment' if name=='fragment' else 'prefix',target)
            transformed_ids={r['id'] for r in valid_transformrows if r['status']=='transformed'}
            transformed_only={key:{'n':len([r for r in value['rows'] if r['id'] in transformed_ids]),
                'payload_word_equivalents':metrics([r['payload_word_equivalents'] for r in value['rows'] if r['id'] in transformed_ids])} for key,value in cv.items()}
            data['compact_static_diagnostic']={'fit_population':300,'validation_population':100,'fit_source_rows':transformrows,
                'validation_source_rows':valid_transformrows,'mining':cm,'validation_parse_errors':cve,'qualified_successors':0,
                'fit':cr,'validation':cv,'validation_transformed_only':transformed_only,'trials':cx,'seal_sha256':sha(packed(cs))}
        result['languages'][language]=data
        write(a.report,result)
    for name,digest in pins.items():
        path=HERE/name if '/' not in name else HERE.parent/name
        if sha(path.read_bytes())!=digest:raise ValueError('Implementation changed during run')
    result['decoder_storage_bytes']={'mixed':len((HERE/'codec.py').read_bytes()),'fragment':len((HERE.parent/'fragment-spelling-v1/codec.py').read_bytes())}
    if a.prior_attempt:
        result['prior_attempt']={'path':str(a.prior_attempt.resolve()),'sha256':sha(a.prior_attempt.read_bytes()),'status':'retained earlier development attempt; not used for selection'}
    result['elapsed_seconds']=time.monotonic()-start;result['max_rss_native_units']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    result['runtime']={'python':sys.version,'platform':sys.platform};result['status']='completed';write(a.report,result)
    print('completed',a.report,flush=True)

if __name__=='__main__':main()
