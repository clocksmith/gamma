"""Bound-name optimization under a fixed shared literal vocabulary."""
import json
import importlib.util
from pathlib import Path
import string
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/'cost-decomposition-v1'))
import analyze
_spec = importlib.util.spec_from_file_location('name_search_codec', HERE.parent/'clusters-v1/search.py')
codec = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(codec)


def records(texts):
    result = subprocess.run(['node', str(HERE/'bindings.cjs')], input=json.dumps(texts), text=True,
                            capture_output=True, check=True)
    return json.loads(result.stdout)


def render(text, record, mapping):
    assert len(set(mapping.values())) == len(mapping)
    assert not set(mapping.values()) & set(record['reserved'])
    edits = sorted((start,end,mapping[n['name']]) for n in record['names'] for start,end in n['spans'])
    out, offset = [], 0
    for start,end,name in edits:
        assert start >= offset
        out.extend((text[offset:start],name)); offset=end
    out.append(text[offset:])
    return ''.join(out)


def optimize(text, record, vocab, sweeps=2):
    """Coordinate substitutions/swaps; score full strings, retain strict improvements."""
    # Acorn positions are UTF-16. Research inputs are ASCII; unsupported text is retained.
    if not text.isascii() or not record['names']:
        return text, {'trials':0,'moves':0,'unsupported':not text.isascii() or record['unsafe']}
    tree = codec.trie(vocab)
    score = lambda source: len(codec.encode_text(source, tree))
    mapping = {n['name']:n['name'] for n in record['names']}
    current, cost, trials, moves = text, score(text), 0, 0
    trace=[]
    for _ in range(sweeps):
        changed = False
        for binding in record['names']:
            name=binding['name']; best=None
            reverse={v:k for k,v in mapping.items()}
            for target in string.ascii_lowercase:
                if target == mapping[name] or target in record['reserved']:
                    continue
                proposal=dict(mapping)
                if target in reverse:
                    proposal[reverse[target]]=mapping[name]
                proposal[name]=target
                candidate=render(text,record,proposal)
                value=score(candidate); trials+=1
                trace.append({'trial':trials,'name':name,'target':target,'selections':value,
                              'sha256':analyze.sha(candidate.encode())})
                key=(value,len(candidate.encode()),candidate)
                if value < cost and (best is None or key < best[0]):
                    best=(key,proposal,candidate)
            if best is not None:
                key,mapping,current=best; cost=key[0]; moves+=1;changed=True
                trace.append({'accepted_mapping':dict(mapping),'selections':cost,'sha256':analyze.sha(current.encode())})
        if not changed:
            break
    return current, {'trials':trials,'moves':moves,'unsupported':False,'_trace':trace}
