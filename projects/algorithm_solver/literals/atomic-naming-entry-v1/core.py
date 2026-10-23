"""Shared exact literal costs, source geometry and unchanged binding guards."""
import os
import sys
_IMPORT_PATH=list(sys.path)
if not __debug__ or os.environ.get('PYTHONOPTIMIZE','') not in ('','0'):
    raise RuntimeError('Normal Python assertions required; -O/PYTHONOPTIMIZE forbidden')
from collections import defaultdict
import importlib.util
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent;LIT=HERE.parent

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

rewrite=module('atomic_binding',LIT/'binding-descent-v1/rewrite.py')
analyze=rewrite.analyze
segment=module('atomic_segment',LIT/'segmentation-audit-v1/segment.py')
# Import the prior palette exclusions/rank without invoking its loader or CLI.
palette=module('atomic_prior_palette',LIT/'palette-names-v1/palette.py')
# Historical loaders prepend their directories; retain our own sibling modules.
sys.path[:]=_IMPORT_PATH
ALPHABET=[chr(i) for i in range(32,127)]+['\n']
canonical=lambda x:json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True)
sha=lambda raw:analyze.sha(raw)
read=lambda p:json.loads(Path(p).read_text())

def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.tmp');temporary.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n');temporary.replace(path)

def order(words):
    alpha={ch:i for i,ch in enumerate(ALPHABET)}
    return sorted(set(words),key=lambda w:(0,alpha[w],'') if w in alpha else (1,0,w))

def digest_sources(texts):return sha(canonical({pid:sha(text.encode()) for pid,text in texts.items()}).encode())

def banned(texts):
    result=set(texts.values());items=list(texts.items())
    for start in range(0,len(items),512):
        batch=dict(items[start:start+512])
        proc=subprocess.run(['/usr/bin/node',str(LIT/'tail-search-v1/structure.cjs')],input=json.dumps(batch),text=True,capture_output=True,check=True)
        result.update(body for row in json.loads(proc.stdout).values() for body in row['bodies'])
    return result


def evaluate(texts,vocab,parent=None):
    vocab=order(vocab);assert 1<=len(vocab)<=256
    delta=set(vocab)^set(parent['vocab']) if parent else None
    plans={}
    for pid,text in texts.items():
        if parent and text==parent['sources'][pid] and not any(word in text for word in delta):
            plans[pid]=parent['plans'][pid]
        else:
            ids=segment.encode(text,vocab,'shortest_min_char');plans[pid]=[vocab[i] for i in ids]
    n=sum(map(len,plans.values()));c=sum(len(word)==1 for parts in plans.values() for word in parts)
    db=len(analyze.dictionary_bytes(vocab));package=db+41*len(texts)+n
    return {'sources':texts,'vocab':vocab,'plans':plans,'N':n,'C':c,'package_bytes':package,
            'dictionary_bytes':db,'source_bytes':sum(len(text.encode()) for text in texts.values())}

def cost(state):return state['N'],state['C'],state['package_bytes']
def tie(state):return cost(state),state['source_bytes'],tuple(state['vocab']),tuple(sorted(state['sources'].items()))
def brief(state):return {k:state[k] for k in ('N','C','package_bytes','dictionary_bytes','source_bytes')}|{'entries':len(state['vocab'])}


def names(vocab,records):
    prior=palette.build_palette(vocab,records,40,12)[:4]
    return list(dict.fromkeys(prior+['aa','ab','ac','ad','ae','af','ag','ah']))


def pattern_at(text,spans,start,end):
    """Complete occurrence containment only, never substring-based renaming."""
    touching=[(a,b) for a,b in spans if a<end and b>start]
    if not touching or any(a<start or b>end for a,b in touching):return None
    parts=[];pos=start
    for a,b in sorted(touching):
        assert pos<=a<b<=end
        parts.extend([text[pos:a],None]);pos=b
    parts.append(text[pos:end]);return parts


def contexts(state,records,cap=16):
    owners=defaultdict(set);scores=defaultdict(int);matches=defaultdict(set);patterns={}
    for pid,text in state['sources'].items():
        rec=records[pid]
        if rec['unsafe'] or not text.isascii():continue
        offsets=[0]
        for word in state['plans'][pid]:offsets.append(offsets[-1]+len(word))
        assert offsets[-1]==len(text)
        variables=[v for v in rec['variables'] if v['eligible']]
        for begin in range(len(offsets)-1):
            for size in range(2,7):
                if begin+size>=len(offsets):break
                start,end=offsets[begin],offsets[begin+size]
                if end-start>160:break
                for variable in variables:
                    parts=pattern_at(text,variable['spans'],start,end)
                    if parts is None:continue
                    key=canonical(parts);patterns[key]=parts;owners[key].add(pid);scores[key]+=size-1
                    matches[key].add((pid,variable['id']))
    ranked=sorted((key for key in owners if len(owners[key])>=2),key=lambda key:(-len(owners[key]),-scores[key],key))[:cap]
    return [{'pattern':patterns[key],'support':len(owners[key]),'savings_rank':scores[key],
             'matches':[[pid,bid] for pid,bid in sorted(matches[key],key=lambda x:(int(x[0]),x[1]))]} for key in ranked]


def make_group(texts,records,context,target,min_support=2):
    assert palette.IDENT.fullmatch(target) and target not in palette.JS_RESERVED
    by_pid=defaultdict(set)
    for pid,bid in context['matches']:by_pid[pid].add(bid)
    updates={};geometry=[]
    for pid in sorted(by_pid,key=int):
        rec=records[pid]
        if rec['unsafe'] or not texts[pid].isascii():continue
        for bid in sorted(by_pid[pid],key=lambda i:(-len(rec['variables'][i]['spans']),i)):
            var=rec['variables'][bid]
            if not var['eligible'] or var['name']==target:continue
            colors=[v['name'] for v in rec['variables']];colors[bid]=target
            if not rewrite.legal(rec,colors):continue
            actual=rewrite.render(texts[pid],rec,colors)
            updates[pid]=actual
            geometry.append({'pid':pid,'binding':bid,'from':var['name'],'to':target,'spans':var['spans'],
                             'before_sha256':sha(texts[pid].encode()),'after_sha256':sha(actual.encode())})
            break
    if not updates:return None
    fragment=''.join(target if part is None else part for part in context['pattern'])
    eligible=len(updates)>=min_support and 2<=len(fragment)<=160 and sum(fragment in text for text in updates.values())>=min_support
    group={'pattern':context['pattern'],'target':target,'geometry':geometry,'updates':updates,'fragment':fragment,'eligible':eligible}
    group['id']=sha(canonical({k:v for k,v in group.items() if k!='updates'}).encode())
    return group


def literal_proposals(state,forbidden):
    owners=defaultdict(set);scores=defaultdict(int)
    for pid,parts in state['plans'].items():
        for start in range(len(parts)):
            for size in range(2,7):
                if start+size>len(parts):break
                word=''.join(parts[start:start+size])
                if len(word.encode())>160:break
                if word not in forbidden and word not in state['vocab']:
                    owners[word].add(pid);scores[word]+=size-1
    words=sorted((w for w in owners if len(owners[w])>=2),key=lambda w:(-scores[w],len(w),w))[:24]
    return [[w] for w in words]+[order(words[i:i+2]) for i in range(min(8,len(words)-1))]


class HardDeadline(BaseException):
    """Cannot be swallowed by a candidate/observation except Exception handler."""
    pass

class LegalityFailure(RuntimeError):pass

class BanLedger:
    def __init__(self):self.variants={};self.forbidden=set();self.encounters=[];self.pending_group=None
    def encounter(self,texts,phase):
        new={}
        for pid,text in texts.items():
            digest=sha(text.encode());key=f'{pid}:{digest}'
            if key not in self.variants:self.variants[key]=text;new[key]=text
        if new:
            self.forbidden.update(banned(new));self.encounters.append({'phase':phase,'variant_keys':list(new)})
    def assert_incumbent(self,state):
        illegal=set(state['vocab'])&self.forbidden
        if illegal:raise LegalityFailure('New accumulated source/body ban invalidates incumbent: '+','.join(sorted(sha(s.encode()) for s in illegal)))
    def receipt(self):return {'variants':self.variants,'banned':sorted(self.forbidden),'encounters':self.encounters,'last_rendered_group':self.pending_group}
