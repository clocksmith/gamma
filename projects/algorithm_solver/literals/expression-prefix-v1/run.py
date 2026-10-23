"""Matched literal versus prefix-expression representation on fixed R sources."""
import argparse
from collections import Counter
import concurrent.futures
import importlib.util
import json
import multiprocessing
from pathlib import Path
import sys
import time
import codec
import search

HERE=Path(__file__).resolve().parent;LIT=HERE.parent
sys.path.insert(0,str(LIT/'cost-decomposition-v1'))
import analyze
_spec=importlib.util.spec_from_file_location('expression_tail_helpers',LIT/'tail-search-v1/search.py')
tail=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(tail)


def forbidden(texts):
    structure=tail.source_structure(texts)
    return set(texts.values())|{b for r in structure.values() for b in r['bodies']}


def aggregate(rows,ids,db,decoder):
    selected=[rows[str(pid)] for pid in ids];s=sum(r['selections'] for r in selected)
    return {'problems':len(ids),'covered':len(selected),'selections':analyze.distribution([r['selections'] for r in selected]),
        'actions':analyze.distribution([r['actions'] for r in selected]),'single_character_fraction':sum(r['single_characters'] for r in selected)/s,
        'constructor_codes':sum(r['constructor_codes'] for r in selected),'constructor_programs':sum(r['constructor_codes']>0 for r in selected),
        'eligible_programs':sum(r['eligible'] for r in selected),'dictionary_bytes':db,
        'packet_bytes':sum(r['packet_bytes'] for r in selected),'framing_bytes':41*len(selected),
        'padding_bits':sum(r['padding_bits'] for r in selected),'payload_bits':sum(r['payload_bits'] for r in selected),
        'package_bytes':db+sum(r['packet_bytes'] for r in selected),
        'package_with_decoder_dependencies':db+sum(r['packet_bytes'] for r in selected)+decoder}


def arm(job):
    width,name,work,out=job['width'],job['arm'],Path(job['work']),Path(job['output']);typed=name=='typed'
    c=json.loads((HERE/'contract.json').read_text());parent=json.loads((LIT/'cost-decomposition-v1/contract.json').read_text())
    fit_ids,val_ids=parent['partition']['dev_fit'],parent['partition']['dev_val']
    fit=analyze.load_sources(work,{**parent,'sources':[r for r in parent['sources'] if r['id'] in set(fit_ids)]})
    nodes=codec.extract(fit);ban=forbidden(fit);constructors,expr_pool,support=search.pool(fit,nodes,ban)
    raw=(work/parent['dictionaries'][str(width)]['relative_path']).read_bytes();assert analyze.sha(raw)==parent['dictionaries'][str(width)]['sha256']
    initial=[codec.literal(x) for x in json.loads(raw)];started=time.monotonic()
    baseline=json.loads((LIT/'cost-decomposition-v1/evidence/results.json').read_text())['arms'][str(width)]
    initial_fit=sum(codec.encode_source(text,nodes[str(pid)],initial)['selections'] for pid,text in fit.items())
    assert initial_fit==baseline['dev_fit']['selections']['total']
    state,info=search.optimize(fit,nodes,initial,width,constructors if typed else [],expr_pool,ban,c['search'],typed)
    folder=out/f'{name}-{2**width}';folder.mkdir()
    analyze.write(folder/'dictionary.json',state['keys']);analyze.write(folder/'trace.json',info.pop('trace'))
    analyze.write(folder/'pool.json',{'constructors':constructors,'expression_literals':expr_pool,'support':support})
    db=codec.dictionary(state['keys']) if typed else codec.literal_dictionary(state['keys'])
    (folder/'dictionary.bin').write_bytes(db)
    analyze.write(folder/'fit-seal.json',{'validation_loaded':False,'dictionary_sha256':analyze.sha(db),
                   'dictionary_json_sha256':analyze.sha((folder/'dictionary.json').read_bytes()),'pool_sha256':analyze.sha((folder/'pool.json').read_bytes())})
    print(json.dumps({'arm':name,'width':width,'fit_selections':state['selections'],'trials':info['trials'],'stop':info['stop']}),flush=True)
    val=analyze.load_sources(work,{**parent,'sources':[r for r in parent['sources'] if r['id'] in set(val_ids)]})
    val_nodes=codec.extract(val);all_nodes={**nodes,**val_nodes};texts={**fit,**val}
    initial_val=sum(codec.encode_source(text,val_nodes[str(pid)],initial)['selections'] for pid,text in val.items())
    assert initial_val==baseline['dev_val']['selections']['total']
    plans={**state['rows'],**{pid:codec.encode_source(text,val_nodes[str(pid)],state['keys']) for pid,text in val.items()}}
    if typed:
        decoded=codec.decode_many(state['keys'],plans,width)
        assert all(decoded[str(pid)]==text for pid,text in texts.items())
    rows={};packets=folder/'packets';packets.mkdir();ctor_set=set(constructors)
    for pid,text in texts.items():
        plan=plans[pid]
        if typed:packet=codec.packet(state['keys'],plan['tokens'],width)
        else:
            vocab=[k[1:] for k in state['keys']];ids={k:i for i,k in enumerate(state['keys'])}
            packet=analyze.encode(vocab,[ids[k] for k in plan['tokens']],width)
            assert analyze.decode(db,packet)==text
            assert len(analyze.shortest_encode(text,vocab))==plan['selections']
        (packets/f'{pid}.bin').write_bytes(packet)
        rows[str(pid)]={'source_sha256':analyze.sha(text.encode()),'packet_sha256':analyze.sha(packet),'encodable':True,
            'selections':plan['selections'],'actions':plan['selections']+1,'single_characters':plan['single_characters'],
            'constructor_codes':plan['constructor_codes'],'packet_bytes':len(packet),'payload_bits':plan['selections']*width,
            'padding_bits':8*(len(packet)-41)-plan['selections']*width,'eligible':any(n['key'] in ctor_set for n in all_nodes[str(pid)])}
    ban|=forbidden(val)
    illegal=[analyze.sha(k[1:].encode()) for k in state['keys'] if k[0]=='L' and k[1:] in ban]
    dependencies=c['decoder_dependencies']['typed' if typed else 'literal'];decoder=sum(Path(p).stat().st_size for p in dependencies)
    result={'arm':name,'width':width,'entries':len(state['keys']),'constructor_entries':sum(k[0]=='C' for k in state['keys']),
        'initial_fit_selections':initial_fit,'initial_validation_selections':initial_val,
        'dictionary_sha256':analyze.sha(db),'dictionary_bytes':len(db),'decoder_dependency_bytes':decoder,
        'illegal_entry_sha256':illegal,'per_problem':rows,'fit':aggregate(rows,fit_ids,len(db),decoder),
        'validation':aggregate(rows,val_ids,len(db),decoder),'search':info,'seconds':time.monotonic()-started,
        'constructor_pool_count':len(constructors),'expression_literal_pool_count':len(expr_pool),
        'fit_eligible_ids':[pid for pid in fit_ids if rows[str(pid)]['eligible']],
        'validation_eligible_ids':[pid for pid in val_ids if rows[str(pid)]['eligible']]}
    analyze.write(folder/'results.json',result);return result


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--work',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    c=json.loads((HERE/'contract.json').read_text())
    for rel,h in c['code_hashes'].items():assert analyze.sha((LIT/rel).read_bytes())==h,rel
    for path,h in c['runtime_files'].items():assert analyze.sha(Path(path).read_bytes())==h,path
    a.output.mkdir(parents=True,exist_ok=False);started=time.monotonic()
    jobs=[{'arm':n,'width':w,'work':str(a.work.resolve()),'output':str(a.output.resolve())} for w in (7,8) for n in ('literal','typed')]
    with concurrent.futures.ProcessPoolExecutor(4,mp_context=multiprocessing.get_context('spawn')) as pool:results=list(pool.map(arm,jobs))
    analyze.write(a.output/'results.json',{'arms':results,'seconds':time.monotonic()-started,'contract_sha256':analyze.sha((HERE/'contract.json').read_bytes())})


if __name__=='__main__':main()
