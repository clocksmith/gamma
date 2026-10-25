"""Pinned metadata and cache restoration; no encoder invocation or source access."""
import hashlib,json
from pathlib import Path

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def pinned(spec):
    p=Path(spec['path'])
    if p.stat().st_size>32*1024**2:raise ValueError('metadata size limit')
    raw=p.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=spec['sha256']:raise ValueError('pinned metadata mismatch')
    def unique(pairs):
        out={}
        for key,value in pairs:
            if key in out:raise ValueError('duplicate metadata key')
            out[key]=value
        return out
    return json.loads(raw,object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite JSON')))

def check_pin(spec):
    if sha(spec['path'])!=spec['sha256']:raise ValueError('artifact hash mismatch')

def first_queries(spec):
    # Deliberately project only identity/text of positions 0..3. No labels,
    # outcomes, subsequent texts, policy search or confirmation loading.
    rows=pinned(spec)['queries']
    if len(rows)!=52:raise ValueError('original development population mismatch')
    return [{'position':i,'query_id':rows[i]['query_id'],'text':rows[i]['text']} for i in range(4)]

def query_identity(rows):
    return [{'position':r['position'],'query_id':r['query_id'],
             'text_sha256':hashlib.sha256(r['text'].encode()).hexdigest()} for r in rows]

def validate_array(a,n,np):
    if a.shape!=(n,1024) or a.dtype!=np.float32 or not np.isfinite(a).all() or not np.allclose(np.linalg.norm(a,axis=1),1,atol=1e-4):
        raise ValueError('invalid normalized cache/query array')

class FullIndex:
    def __init__(self,array,np):self.array=array;self.np=np
    def scores(self,query):
        validate_array(query,1,self.np)
        return (query@self.array.T)[0]

def restore_index(freeze,np):
    """Rebuild exactly54 replacements over4081 title vectors; no query vectors."""
    ids=freeze['stable_ids'];chunks=[]
    if len(ids)!=4081 or len(set(ids))!=4081:raise ValueError('complete unique population')
    if [c['start'] for c in freeze['baseline_chunks']]!=list(range(0,4081,64)):raise ValueError('baseline chunk coverage')
    replacements=freeze['replacement_positions']
    if len(replacements)!=54 or len(set(replacements))!=54 or any(type(i)is not int or not 0<=i<4081 for i in replacements):raise ValueError('exact54 delta positions')
    for c in freeze['baseline_chunks']:
        info=pinned(c['receipt']);check_pin(c['array']);start=c['start'];expected=ids[start:start+64]
        if info['ids']!=expected or info['start']!=start or info['sha256']!=c['array']['sha256']:raise ValueError('baseline binding')
        flags=info['request']['truncated']
        if len(flags)!=len(expected) or any(type(x)is not bool for x in flags) or any(v for i,v in enumerate(flags) if start+i not in replacements):raise ValueError('truncated reused document')
        a=np.load(c['array']['path'],allow_pickle=False);validate_array(a,len(expected),np);chunks.append(a)
    array=np.concatenate(chunks);validate_array(array,4081,np)
    if [c['start'] for c in freeze['delta_chunks']]!=list(range(0,54,4)):raise ValueError('delta coverage')
    for c in freeze['delta_chunks']:
        info=pinned(c['receipt']);check_pin(c['array']);start=c['start'];positions=replacements[start:start+4]
        if (info['ids']!=[ids[i] for i in positions] or info['binding_sha256']!=c['binding_sha256'] or
            info['array_sha256']!=c['array']['sha256']):raise ValueError('delta binding')
        flags=info['request']['truncated']
        if len(flags)!=len(positions) or any(x is not False for x in flags):raise ValueError('truncated delta document')
        a=np.load(c['array']['path'],allow_pickle=False);validate_array(a,len(positions),np);array[positions]=a
    validate_array(array,4081,np)
    return FullIndex(array,np)
