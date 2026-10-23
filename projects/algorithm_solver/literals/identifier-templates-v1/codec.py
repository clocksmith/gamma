"""Exact identifier-template encoder; each constructor and distinct argument consumes IDs."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess

HERE=Path(__file__).resolve().parent
ALPHABET=[chr(i) for i in range(32,127)]+['\n']
canonical=lambda x:json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True)


def literal(text):return 'L'+text
def constructor(spec):return 'C'+canonical(spec)


def order(keys):
    letters={literal(s):i for i,s in enumerate(ALPHABET)}
    return sorted(set(keys),key=lambda k:(0,letters[k]) if k in letters else (1,k[1:]) if k.startswith('L') else (2,k[1:]))


def dictionary(keys):
    entries=[['L',k[1:]] if k[0]=='L' else ['C',json.loads(k[1:])] for k in keys]
    return b'ITD1'+canonical(entries).encode()


def literal_dictionary(keys):
    assert all(k[0]=='L' for k in keys)
    fields=[b'LTD1',struct.pack('>I',len(keys))]
    for k in keys:
        raw=k[1:].encode();fields.extend([struct.pack('>I',len(raw)),raw])
    return b''.join(fields)


def extract(texts):
    result=subprocess.run(['node',str(HERE/'extract.cjs')],input=json.dumps(texts),text=True,capture_output=True,check=True)
    out=json.loads(result.stdout)
    for nodes in out.values():
        for node in nodes:node['key']=constructor(node['spec']) if node['spec'] else None
    return out


def encode_source(text,nodes,keys):
    """Body DP plus typed-expression subtree DP. Literal child must span one whole AST expression."""
    keys=order(keys);rank={k:i for i,k in enumerate(keys)};present=set(keys)
    # Templates are nonrecursive: one constructor then one literal per distinct identifier.
    edges={}
    for node in nodes:
        key=node['key']
        if key is None or key not in present:continue
        args=[literal(x) for x in node['args']]
        if all(arg in present for arg in args):
            edges.setdefault(node['start'],[]).append((node['end'],([key]+args,[])))
    trie={}
    for key in keys:
        if key[0]!='L':continue
        node=trie
        for char in key[1:]:node=node.setdefault(char,{})
        node[None]=key
    size=len(text);cost=[size+1]*(size+1);cost[size]=0;next_edge=[None]*size
    def suffix(i):
        tokens=[]
        while i<size:
            edge=next_edge[i]
            if edge is None:raise ValueError('unreachable suffix')
            j,head=edge;tokens.extend(head[0]);i=j
        return tokens
    for i in range(size-1,-1,-1):
        options=list(edges.get(i,[]));node=trie;j=i
        while j<size and text[j] in node:
            node=node[text[j]];j+=1
            if None in node:options.append((j,([node[None]],[(i,j,node[None])])))
        for j,head in options:
            total=len(head[0])+cost[j]
            if total>size:continue
            take=total<cost[i]
            if total==cost[i]:
                old_j,old_head=next_edge[i]
                first,old_first=rank[head[0][0]],rank[old_head[0][0]]
                take=first<old_first
                if first==old_first:
                    take=tuple(rank[k] for k in head[0]+suffix(j))<tuple(rank[k] for k in old_head[0]+suffix(old_j))
            if take:cost[i]=total;next_edge[i]=(j,head)
    if next_edge[0] is None:raise ValueError('unencodable source')
    tokens=[];spans=[];i=0
    while i<size:
        j,head=next_edge[i];tokens.extend(head[0]);spans.extend(head[1]);i=j
    fixed_bytes=repeated_bytes=argument_codes=0;offset=0
    while offset<len(tokens):
        key=tokens[offset];offset+=1
        if key[0]=='C':
            spec=json.loads(key[1:]);args=[tokens[offset+i][1:] for i in range(spec['arity'])];offset+=spec['arity']
            fixed_bytes+=sum(map(len,spec['parts']));repeated_bytes+=sum(len(args[i]) for i in spec['uses'])-sum(map(len,args));argument_codes+=spec['arity']
    return {'tokens':tokens,'literal_spans':sorted(spans),'selections':len(tokens),
            'fixed_template_bytes':fixed_bytes,'repeated_identifier_bytes':repeated_bytes,'argument_codes':argument_codes,'free_bytes':fixed_bytes+repeated_bytes,
            'single_characters':sum(k[0]=='L' and len(k[1:])==1 for k in tokens),
            'constructor_codes':sum(k[0]=='C' for k in tokens)}


def packet(keys,tokens,width):
    assert 1<=len(keys)<=2**width and len(set(keys))==len(keys)
    ids={k:i for i,k in enumerate(keys)};value=0;bits=0;payload=bytearray()
    for key in tokens:
        value=(value<<width)|ids[key];bits+=width
        while bits>=8:
            bits-=8;payload.append((value>>bits)&255)
    if bits:payload.append((value<<(8-bits))&255)
    return b'ITB1'+bytes([width])+hashlib.sha256(dictionary(keys)).digest()+struct.pack('>I',len(tokens))+bytes(payload)


def decode_many(keys,rows,width):
    import base64
    request={'dictionary':base64.b64encode(dictionary(keys)).decode(),'packets':{str(pid):base64.b64encode(packet(keys,r['tokens'],width)).decode() for pid,r in rows.items()}}
    result=subprocess.run(['node',str(HERE/'decoder.cjs')],input=json.dumps(request),text=True,capture_output=True,check=True)
    return json.loads(result.stdout)
