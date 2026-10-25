"""Bounded fit-only substring search; never executes source programs."""
from __future__ import annotations
import argparse
from bisect import bisect_left
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import time

HERE=Path(__file__).resolve().parent
LIT=HERE.parent
MAX_POOL=2048
MAX_ROUNDS=8
MAX_EVALUATIONS=1024
CPU_CAP=120

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
compare=module('compact_measure',LIT/'readable-joint-blocks-v1/compare.py')
transfer=module('compact_transfer',LIT/'readable-joint-blocks-v1/transfer.py')
ALPHABET=compare.ALPHABET

def sha(data):return hashlib.sha256(data).hexdigest()
def encoded(value):return (json.dumps(value,sort_keys=True,indent=2)+'\n').encode()
def write(path,value):path.write_bytes(encoded(value))

def lexical_tokens(text):
    """Small conservative lexer for frozen declaration bodies, never evaluation.

    Quoted strings, comments and expression-position regexes are opaque. Template
    literals support only plain text and identifier interpolation; others fail closed.
    """
    tokens=[];i=0;previous=None
    regex_prefix={'=', '(', '[', '{', ',', ':', ';', '!', '?', 'return', '=>', '&&', '||'}
    while i<len(text):
        c=text[i]
        if c.isspace():i+=1;continue
        if c=='`':
            match=re.match(r'`(?:[^`\\$]|\\.|\$\{[A-Za-z_$][A-Za-z0-9_$]*\})*`',text[i:])
            if match is None:raise ValueError('complex template requires a full parser')
            tokens.append(('STRING',i,i+len(match.group())));i+=len(match.group());previous='STRING';continue
        if text.startswith('//',i):
            end=text.find('\n',i);i=len(text) if end<0 else end+1;continue
        if text.startswith('/*',i):
            end=text.find('*/',i+2)
            if end<0:raise ValueError('unterminated comment')
            i=end+2;continue
        start=i
        if c in ("'",'"'):
            quote=c;i+=1
            while i<len(text) and text[i]!=quote:
                i+=2 if text[i]=='\\' else 1
            if i>=len(text):raise ValueError('unterminated string')
            i+=1;token='STRING'
        elif c=='/' and previous in regex_prefix:
            i+=1;inside=False
            while i<len(text):
                if text[i]=='\\':i+=2;continue
                if text[i]=='[':inside=True
                elif text[i]==']':inside=False
                elif text[i]=='/' and not inside:break
                i+=1
            if i>=len(text):raise ValueError('unterminated regex')
            i+=1
            while i<len(text) and text[i].isalpha():i+=1
            token='REGEX'
        elif c.isalpha() or c in '_$':
            i+=1
            while i<len(text) and (text[i].isalnum() or text[i] in '_$'):i+=1
            token=text[start:i]
        else:
            i+=1;token=c
            if text[start:i+1] in ('=>','&&','||'):i+=1;token=text[start:i]
        tokens.append((token,start,i));previous=token
    return tokens

def forbidden(texts):
    result=set()
    for text in texts.values():
        tokens=lexical_tokens(text)
        starts=[i for i in range(len(tokens)-2) if tokens[i][0]=='function' and tokens[i+1][0]=='solve' and tokens[i+2][0]=='(']
        if len(starts)!=1:raise ValueError('exactly one named solve declaration required')
        at=starts[0]+2;depth=0
        while at<len(tokens):
            token=tokens[at][0];depth+=(token=='(')-(token==')');at+=1
            if depth==0:break
        if at>=len(tokens) or tokens[at][0]!='{':raise ValueError('solve body missing')
        opening=tokens[at][1];depth=0;closing=None
        while at<len(tokens):
            token,start,end=tokens[at];depth+=(token=='{')-(token=='}');at+=1
            if depth==0:closing=end;break
        if closing is None:raise ValueError('unbalanced solve body')
        body=text[opening:closing]
        definition=text[tokens[starts[0]][1]:closing]
        result.update((text,text.strip(),definition,body,body[1:-1],body[1:-1].strip()))
    return result

def build_pool(texts,banned,stats=None):
    suffixes=sorted((text[i:i+64],pid) for pid,text in texts.items() for i in range(len(text)-1))
    repeated=set()
    for (left,pid),(right,qid) in zip(suffixes,suffixes[1:]):
        if pid==qid:continue
        length=0
        while length<min(len(left),len(right)) and left[length]==right[length]:length+=1
        repeated.update(left[:end] for end in range(2,length+1) if left[:end] not in banned)
    keys=[s for s,_ in suffixes]
    counts={s:bisect_left(keys,s+chr(0x10ffff))-bisect_left(keys,s) for s in repeated}
    ranked=sorted(repeated,key=lambda s:(-counts[s]*(len(s)-1),len(s),s))
    if stats is not None:stats.update(eligible_repeated_substrings=len(ranked),retained=min(MAX_POOL,len(ranked)),excluded_by_fit_only_rank=max(0,len(ranked)-MAX_POOL))
    return ranked[:MAX_POOL]

class Graph:
    def __init__(self,texts):
        self.texts=texts;self.occ={}
    def occurrence(self,piece):
        if piece not in self.occ:
            found={}
            for pid,text in self.texts.items():
                positions=[];at=text.find(piece)
                while at>=0:positions.append(at);at=text.find(piece,at+1)
                if positions:found[pid]=positions
            self.occ[piece]=found
        return self.occ[piece]
    def score(self,vocab,previous=None,changed=()):
        affected=set(self.texts) if previous is None else set().union(*(set(self.occurrence(p)) for p in changed))
        rows={} if previous is None else dict(previous)
        for pid in affected:
            text=self.texts[pid];edges=[[] for _ in text]
            for index,piece in enumerate(vocab):
                for at in self.occurrence(piece).get(pid,[]):edges[at].append((index,at+len(piece)))
            costs=[0]*(len(text)+1);choice=[None]*len(text)
            for at in range(len(text)-1,-1,-1):
                count,index,end=min((1+costs[end],index,end) for index,end in edges[at])
                costs[at]=count;choice[at]=(index,end)
            at=0;sequence=[];characters=[]
            while at<len(text):
                index,end=choice[at];sequence.append(vocab[index])
                if len(vocab[index])==1:characters.append(at)
                at=end
            rows[pid]={'selections':len(sequence),'characters':len(characters),'used':sequence,'character_positions':characters}
        return rows

def objective(rows,arm):
    s=sum(r['selections'] for r in rows.values());c=sum(r['characters'] for r in rows.values())
    return (s,c) if arm=='selection' else (max(0,10*c-s),s,c)

def optimize(texts,initial,pool,capacity,arm):
    started=time.process_time();graph=Graph(texts)
    vocab=ALPHABET+sorted(initial[96:]);rows=graph.score(vocab)
    initial_objective=objective(rows,arm);selection_ceiling=sum(r['selections'] for r in rows.values());trace=[];evaluations=0;termination='round-cap'
    for round_index in range(MAX_ROUNDS):
        current=objective(rows,arm)
        usage={p:sum(r['used'].count(p) for r in rows.values()) for p in vocab[96:]}
        removals=sorted(vocab[96:],key=lambda p:(usage[p],-len(p),p))[:8]
        def proposal_score(piece):
            occurrences=graph.occurrence(piece)
            if arm=='selection':return sum(len(x) for x in occurrences.values())*(len(piece)-1)
            return sum(sum(start<=at<start+len(piece) for at in rows[pid]['character_positions']) for pid,starts in occurrences.items() for start in starts)
        additions=sorted((p for p in pool if p not in vocab),key=lambda p:(-proposal_score(p),len(p),p))[:24]
        best=None
        for addition in additions:
            for removal in ([None] if len(vocab)<capacity else [])+removals:
                if evaluations>=MAX_EVALUATIONS:break
                if time.process_time()-started>CPU_CAP:raise TimeoutError('frozen CPU budget exhausted; no partial arm')
                learned=(set(vocab[96:])-{removal})|{addition}
                candidate=ALPHABET+sorted(learned)
                candidate_rows=graph.score(candidate,rows,(addition,) if removal is None else (addition,removal))
                evaluations+=1;score=objective(candidate_rows,arm)
                if score<current and (arm=='selection' or sum(r['selections'] for r in candidate_rows.values())<=selection_ceiling):
                    record=(score,tuple(candidate),candidate_rows,addition,removal)
                    if best is None or record[:2]<best[:2]:best=record
            if evaluations>=MAX_EVALUATIONS:break
        if best is not None:
            score,candidate,rows,addition,removal=best;vocab=list(candidate)
            # Independent full scorer verifies accepted exact paths, not just totals.
            for pid,text in texts.items():
                actual=[vocab[i] for i in compare.scorer.shortest_encode(text,vocab)]
                if actual!=rows[pid]['used']:raise AssertionError('incremental DAG drift')
            trace.append({'round':round_index,'before':current,'after':score,'add':addition,'remove':removal})
        if evaluations>=MAX_EVALUATIONS:termination='evaluation-cap';break
        if best is None:termination='no-improving-proposal';break
    return vocab,{'initial_objective':initial_objective,'final_objective':objective(rows,arm),'evaluations':evaluations,'trace':trace,'termination':termination,'cpu_seconds':time.process_time()-started}

def policy():
    spec=transfer.derive_manifest()
    fit=spec['partition']['dev_fit'];val=spec['partition']['dev_val']
    if len(fit)!=300 or len(val)!=100 or len(set(fit+val))!=400:raise ValueError('partition mismatch')
    return spec

def verified(root,row):
    raw=transfer.read_relative(root,row['path'])
    if sha(raw)!=row['sha256']:raise ValueError('allowlisted input hash drift')
    return raw

def check_receipt(root,spec):
    receipt=transfer.parse(transfer.read_relative(root,'transfer-receipt.json'))
    if (receipt.get('partition')!=spec['partition'] or receipt.get('payload_files')!=1202 or
        receipt.get('manifest_sha256')!=sha((json.dumps(spec,indent=2)+'\n').encode()) or
        receipt.get('final_heldout_payload_files_opened')!=0 or receipt.get('protected_payload_files_opened')!=0):
        raise ValueError('transfer receipt scope mismatch')

def sources(root,spec,partition):
    allowed=set(spec['partition'][partition]);rows=[r for r in spec['files'] if r['kind']=='source' and r['id'] in allowed]
    if len(rows)!=len(allowed):raise ValueError('source population incomplete')
    return {str(r['id']):verified(root,r).decode() for r in rows}

def pins():
    files=[HERE/'search.py',HERE/'test_search.py',HERE/'FREEZE.md',LIT/'readable-joint-blocks-v1/compare.py',LIT/'readable-joint-blocks-v1/transfer.py',compare.CODEC_FILE,compare.SCORER_FILE]
    return {str(p.relative_to(LIT)):sha(p.read_bytes()) for p in files}

def freeze(root,output):
    if output.resolve().is_relative_to(LIT.parents[1]):raise ValueError('private experiment output must be outside repository')
    spec=policy();check_receipt(root,spec)
    contract={'schema':'gamma.compact-search.freeze.v1','code':pins(),'partition':spec['partition'],
              'sources_and_dictionaries':[r for r in spec['files'] if r['kind'] in ('source','dictionary')],
              'max_pool':MAX_POOL,'max_rounds':MAX_ROUNDS,'max_evaluations':MAX_EVALUATIONS,'cpu_cap_seconds':CPU_CAP,
              'arms':['selection','character-budget'],'capacities':[128,256],
              'protected_access':False,'candidate_execution':False,'m1_qualified':False}
    output.mkdir(parents=True,exist_ok=False);write(output/'contract.json',contract)
    return contract

def run(root,frozen,output):
    if output.resolve().is_relative_to(LIT.parents[1]):raise ValueError('private outputs must stay outside repository')
    contract=transfer.parse((frozen/'contract.json').read_bytes())
    if contract['code']!=pins():raise ValueError('code changed after freeze')
    spec=policy();check_receipt(root,spec)
    if contract['partition']!=spec['partition'] or contract['sources_and_dictionaries']!=[r for r in spec['files'] if r['kind'] in ('source','dictionary')]:raise ValueError('frozen input policy drift')
    output.mkdir(parents=True,exist_ok=False)
    report={'schema':'gamma.compact-search.results.v1','status':'running','candidate_execution':False,'protected_access':False,'m1_qualified':False,'contract_sha256':sha((frozen/'contract.json').read_bytes()),'fits':{},'profiles':[]}
    write(output/'contract.json',contract)
    try:
        texts=sources(root,spec,'dev_fit');compare.validate_texts(texts)
        banned=forbidden(texts);pool_stats={};pool=build_pool(texts,banned,pool_stats)
        write(output/'pool.json',{'entries':pool,**pool_stats,'selection':'fit-only occurrence-saving top2048; discarded candidates may improve character objective','scope':'no global optimality or infeasibility claim'})
        vocabularies={}
        for entry in spec['files']:
            if entry['kind']!='dictionary':continue
            capacity=entry['width'];initial=transfer.parse(verified(root,entry))
            if initial[:96]!=ALPHABET or len(initial)>capacity or len(set(initial))!=len(initial):raise ValueError('pinned dictionary shape mismatch')
            if set(initial)&banned:raise ValueError('pinned dictionary contains complete fit source/body')
            vocabularies[f'{capacity}-baseline']=initial
            for arm in contract['arms']:
                name=f'{capacity}-{arm}'
                vocabulary,trace=optimize(texts,initial,pool,capacity,arm)
                vocabularies[name]=vocabulary;report['fits'][name]=trace
                write(output/f'{name}-dictionary.json',vocabulary)
                write(output/'progress.json',report)
        # All four arms sealed together before validation bytes are opened.
        seal={'dictionaries':{name:sha(encoded(v)) for name,v in vocabularies.items()},'fit_ids':sorted(texts),'validation_opened':False}
        write(output/'sealed.json',seal)
        validation=sources(root,spec,'dev_val');compare.validate_texts(validation)
        for partition,values in (('dev_fit',texts),('dev_val',validation)):
            complete=forbidden(values)
            for name,vocab in vocabularies.items():
                capacity=int(name.split('-')[0]);width=capacity.bit_length()-1
                profile,binary=compare.measure(values,vocab,width)
                profile['whole_source_or_body_entries']=len(set(vocab)&complete)
                arm_dir=output/f'{partition}-{name}';arm_dir.mkdir()
                (arm_dir/'dictionary.ltd').write_bytes(binary['dictionary'])
                for pid,packet in binary['packets'].items():(arm_dir/f'{pid}.ltv').write_bytes(packet)
                write(arm_dir/'profile.json',profile)
                report['profiles'].append({'partition':partition,'name':name,**{k:v for k,v in profile.items() if k not in ('per_problem','entry_problem_support','reused_noncharacter_entries')}})
        if contract['code']!=pins():raise ValueError('code changed during experiment')
        report['status']='completed'
    except Exception as error:
        report['status']='failed';report['failure']={'type':type(error).__name__,'reason':str(error)}
        write(output/'results.json',report);raise
    write(output/'results.json',report);return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    for name in ('freeze','run'):
        p=sub.add_parser(name);p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
        if name=='run':p.add_argument('--freeze',type=Path,required=True)
    args=parser.parse_args()
    result=freeze(args.root,args.output) if args.command=='freeze' else run(args.root,args.freeze,args.output)
    print(json.dumps({'status':result.get('status','frozen'),'output':str(args.output)}))
