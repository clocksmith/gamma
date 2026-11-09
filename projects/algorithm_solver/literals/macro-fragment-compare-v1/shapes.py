"""Mine reusable exact spans and fixed-arity AST shells, without executing code."""
import ast
import hashlib
from collections import defaultdict, Counter
import io
import itertools
import json
import subprocess
import tokenize
from pathlib import Path


def python_shape(source):
    lines=source.splitlines(keepends=True); starts=[0]
    for line in lines: starts.append(starts[-1]+len(line.encode()))
    def span(n): return (starts[n.lineno-1]+n.col_offset, starts[n.end_lineno-1]+n.end_col_offset)
    tree=ast.parse(source);nodes=[];banned=[]
    for n in ast.walk(tree):
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
            banned.append(span(n))
            if n.body: banned.append((span(n.body[0])[0],span(n.body[-1])[1]))
        if hasattr(n,'end_lineno') and n.end_lineno and not isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
            children=[span(c) for c in ast.iter_child_nodes(n) if getattr(c,'end_lineno',None)]
            nodes.append((*span(n),children,type(n).__name__))
    def offset(pos):
        row,col=pos
        return starts[row-1]+len(lines[row-1][:col].encode()) if row<=len(lines) else starts[-1]
    tokens=[]
    for t in tokenize.generate_tokens(io.StringIO(source).readline):
        if t.type not in (tokenize.ENDMARKER,tokenize.ENCODING,tokenize.INDENT,tokenize.DEDENT,tokenize.COMMENT) and t.string:
            a,b=offset(t.start),offset(t.end)
            if a<b:tokens.append((a,b))
    return {'tokens':tokens,'nodes':nodes,'banned':banned}


def shapes(sources,language):
    if language=='python':
        out={};errors={}
        for pid,s in sources.items():
            try:out[pid]=python_shape(s)
            except (SyntaxError,ValueError,tokenize.TokenError) as e:errors[pid]=str(e)
        return out,errors
    p=subprocess.run(['node','--expose-internals',str(Path(__file__).with_name('js_shapes.cjs'))],input=json.dumps(sources),text=True,capture_output=True,check=True,timeout=60)
    return json.loads(p.stdout),{}


def occurrences(raw,shape,banned):
    result=set()
    for a,b,children,kind in shape['nodes']:
        if b-a>512 or raw[a:b].strip() in banned:continue
        children=sorted(set(map(tuple,children)))
        if not 1<=len(children)<=4 or any(x<a or y>b or x>=y or (x,y)==(a,b) for x,y in children):continue
        if any(children[i][1]>children[i+1][0] for i in range(len(children)-1)):continue
        variants=[children]+[[c] for c in children]
        for holes in variants:
            parts=[];last=a
            for x,y in holes:parts.append(raw[last:x]);last=y
            parts.append(raw[last:b]);parts=tuple(parts)
            if 2<=sum(map(len,parts))<=160 and b''.join(parts).strip():
                result.add((a,b,parts,tuple(holes)))
    return sorted(result)


def mine(sources,metadata,original_banned=()):
    banned=set(original_banned)
    for pid,source in sources.items():
        raw=source.encode();banned.add(raw.strip())
        for a,b in metadata.get(pid,{}).get('banned',[]):banned.add(raw[a:b].strip())
    owners=defaultdict(set);counts=Counter();macroowners=defaultdict(set);macrocounts=Counter();all_occ={}
    for pid,source in sources.items():
        raw=source.encode();owner=hashlib.sha256(raw).hexdigest();shape=metadata.get(pid,{'tokens':[],'nodes':[]});seen=Counter()
        tokens=shape['tokens']
        for i,(a,_) in enumerate(tokens):
            for j in range(i,min(i+8,len(tokens))):
                b=tokens[j][1];part=raw[a:b]
                if len(part)>160:break
                if len(part.decode())>=2 and part.strip() and not any(x and x in part.strip() for x in banned):seen[part]+=1
        for part,n in seen.items():owners[part].add(owner);counts[part]+=n
        all_occ[pid]=occurrences(raw,shape,banned)
        for _,_,parts,_ in all_occ[pid]:macroowners[parts].add(owner);macrocounts[parts]+=1
    literals=[p for p in owners if len(owners[p])>=2]
    # A reproducible shortlist, not a claim of optimal dictionary selection.
    literals.sort(key=lambda p:(-(len(p)*9-8)*counts[p],-len(owners[p]),p))
    macros=[p for p in macroowners if len(macroowners[p])>=2]
    macros.sort(key=lambda p:(-(sum(map(len,p))*9-8*len(p))*macrocounts[p],p))
    support={p:len(v) for p,v in owners.items()}
    support.update({p:len(v) for p,v in macroowners.items()})
    return literals,macros,all_occ,banned,support
