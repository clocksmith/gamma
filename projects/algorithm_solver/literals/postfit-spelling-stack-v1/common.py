"""Item46 fixed-order adapter and isolated item41 authorities; no corpus loader."""
import os
if not __debug__ or os.environ.get('PYTHONOPTIMIZE','') not in ('','0'):
    raise RuntimeError('Normal Python assertions required')
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent;LIT=HERE.parent
ANCHORS=('24','43N','43W');POLICIES=('canonical','shortest_min_char')
_prior={}
def prior(name):
    if name in _prior:return _prior[name]
    deps={'engine':['core'],'metrics':['core'],'qualification':['core'],
          'run':['core','engine','metrics','qualification'],'report':['core']}.get(name,[])
    loaded={dep:prior(dep) for dep in deps};saved={dep:sys.modules.get(dep) for dep in deps};paths=list(sys.path)
    try:
        sys.modules.update(loaded)
        module_name='postfit_prior41_'+name
        spec=importlib.util.spec_from_file_location(module_name,LIT/'atomic-naming-entry-v1'/(name+'.py'))
        module=importlib.util.module_from_spec(spec);sys.modules[module_name]=module;spec.loader.exec_module(module)
        _prior[name]=module;return module
    finally:
        sys.path[:]=paths
        for dep,value in saved.items():
            if value is None:sys.modules.pop(dep,None)
            else:sys.modules[dep]=value

p=prior('core')
canonical=p.canonical;sha=p.sha;read=p.read;write=p.write;analyze=p.analyze;segment=p.segment
rewrite=p.rewrite;names=p.names;contexts=p.contexts;make_group=p.make_group
BanLedger=p.BanLedger;LegalityFailure=p.LegalityFailure;HardDeadline=p.HardDeadline
cost=p.cost;tie=p.tie;brief=p.brief
hashfile=lambda path:sha(Path(path).read_bytes())

def evaluate(texts,vocab,parent=None):
    """Exact supplied ID order; never call item41.evaluate's sorting wrapper."""
    assert isinstance(vocab,list) and 1<=len(vocab)<=256 and len(vocab)==len(set(vocab)) and all(vocab)
    plans={}
    for pid,text in texts.items():
        if parent and vocab==parent['vocab'] and text==parent['sources'][pid]:plans[pid]=parent['plans'][pid]
        else:plans[pid]=[vocab[i] for i in segment.encode(text,vocab,'shortest_min_char')]
    n=sum(map(len,plans.values()));chars=sum(len(w)==1 for words in plans.values() for w in words)
    db=len(analyze.dictionary_bytes(vocab))
    return {'sources':dict(texts),'vocab':list(vocab),'plans':plans,'N':n,'C':chars,
            'package_bytes':db+41*len(texts)+n,'dictionary_bytes':db,'source_bytes':sum(len(t.encode()) for t in texts.values())}

def check_sources(texts,ids,config):
    assert set(texts)==set(map(str,ids))
    for pid,text in texts.items():assert sha(text.encode())==config['source_qualification'][pid]['source_sha256']

def verify_public(config):
    assert config.get('active') is True,'Inactive execution contract'
    assert config.get('source_bound') is True,'Missing both independently recorded item43 parents'
    for rel,digest in config['code_hashes'].items():assert hashfile(LIT/rel)==digest,rel
    for path,digest in config['runtime_files'].items():assert hashfile(path)==digest,path

def checked_read(work,binding):
    path=Path(work)/binding['path'];assert hashfile(path)==binding['sha256']
    return read(path)

def dictionary(work,anchor,config):
    binding=config['dictionaries'][anchor];vocab=checked_read(work,binding)
    assert isinstance(vocab,list) and len(vocab)==len(set(vocab))
    if binding['entries'] is not None:assert len(vocab)==binding['entries']
    assert 1<=len(vocab)<=256 and all(vocab)
    assert sum(len(w)==1 for w in vocab)==binding['character_entries']
    if binding.get('binary_sha256') is not None:assert sha(analyze.dictionary_bytes(vocab))==binding['binary_sha256']
    return vocab

def global_ledger(ledgers,dictionaries):
    """Union includes rejected variants; no member dictionary gets an exemption."""
    variants={};bans=set();origins=[]
    for anchor,ledger in ledgers:
        for key,text in ledger['variants'].items():
            assert key.endswith(':'+sha(text.encode()))
            assert key not in variants or variants[key]==text
            variants[key]=text
        bans.update(ledger['banned']);origins.append({'anchor':anchor,'ledger_sha256':sha(canonical(ledger).encode())})
    illegal={anchor:sorted(sha(w.encode()) for w in set(vocab)&bans) for anchor,vocab in dictionaries.items()}
    return {'variants':variants,'banned':sorted(bans),'origins':origins,'illegal_entry_sha256':illegal,
            'legal':not any(illegal.values())}
