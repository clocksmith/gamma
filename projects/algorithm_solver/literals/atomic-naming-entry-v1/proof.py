"""Invented-source mechanism proof only; no corpus loader, runner or search."""
import importlib.util
import sys
_IMPORT_PATH=list(sys.path)
from itertools import product
import json
from pathlib import Path
import struct
import subprocess

HERE=Path(__file__).resolve().parent;LIT=HERE.parent
spec=importlib.util.spec_from_file_location('atomic_naming_rewrite',LIT/'binding-descent-v1/rewrite.py')
rewrite=importlib.util.module_from_spec(spec);spec.loader.exec_module(rewrite)
sys.path[:]=_IMPORT_PATH
ALPHABET=[chr(i) for i in range(32,127)]+['\n']


def order(words):
    alpha={ch:i for i,ch in enumerate(ALPHABET)}
    return sorted(set(words),key=lambda s:(0,alpha[s],'') if s in alpha else (1,0,s))


def encode(text,words):
    """Exact (N,C,complete ID sequence), with independent literal packet replay."""
    best=[None]*(len(text)+1);best[-1]=(0,0,())
    for pos in range(len(text)-1,-1,-1):
        for i,word in enumerate(words):
            end=pos+len(word)
            if text.startswith(word,pos) and best[end] is not None:
                n,c,ids=best[end];candidate=(n+1,c+int(len(word)==1),(i,)+ids)
                if best[pos] is None or candidate<best[pos]:best[pos]=candidate
    if best[0] is None:raise ValueError('coverage failure')
    return best[0]


def score(texts,words):
    words=order(words);assert len(words)<=256
    db=rewrite.analyze.dictionary_bytes(words)
    rows={};packets=0
    for pid,text in texts.items():
        n,c,ids=encode(text,words)
        packet=rewrite.analyze.encode(words,list(ids),8)
        assert rewrite.analyze.decode(db,packet)==text
        packets+=len(packet);rows[pid]={'N':n,'C':c,'packet_bytes':len(packet),'source_bytes':len(text.encode())}
    n=sum(r['N'] for r in rows.values());c=sum(r['C'] for r in rows.values())
    decoder=sum((LIT/p).stat().st_size for p in ('literals.py','pass2/working/bitpack.py'))
    return {'entries':len(words),'N':n,'C':c,'actions':n+len(texts),'source_bytes':sum(r['source_bytes'] for r in rows.values()),
            'dictionary_bytes':len(db),'packet_bytes':packets,'package_bytes':len(db)+packets,
            'decoder_bytes':decoder,'decoder_inclusive_bytes':len(db)+packets+decoder,'per_program':rows}


def lex(row):return row['N'],row['C'],row['package_bytes']


def fixture():
    texts={str(i):f'function solve({name}){{let z={constant};return {name}+{name}+z;}}'
           for i,(name,constant) in enumerate(product('abcd',(0,1)))}
    records=rewrite.records(texts);renamed={}
    for pid,text in texts.items():
        rec=records[pid];assert not rec['unsafe']
        colors=[v['name'] for v in rec['variables']]
        target=next(v for v in rec['variables'] if v['name'] in 'abcd' and v['eligible'])
        colors[target['id']]='aa';assert rewrite.legal(rec,colors)
        renamed[pid]=rewrite.render(text,rec,colors)
    words=set(ALPHABET+['function solve(','){let z=',';return ','+z;}']);fillers=[]
    # Two-character unused fillers keep replacement storage fully charged;
    # the dictionary-only companion cannot win by discarding long junk strings.
    for a,b in product('!"#$%&*,-./:<>?@[]^_`|~',repeat=2):
        word=a+b
        if all(word not in text for text in [*texts.values(),*renamed.values()]):
            words.add(word);fillers.append(word)
            if len(words)==256:break
    assert len(words)==256
    return texts,renamed,order(words),fillers


def proof():
    original,renamed,seed,fillers=fixture()
    dictionaries={'seed':seed,'label':order((set(seed)-set(fillers[:1]))|{'aa'}),
                  'context':order((set(seed)-set(fillers[:2]))|{'aa','aa+aa'}),
                  'context_without_label':order((set(seed)-set(fillers[:1]))|{'aa+aa'}),
                  'literal_control':order((set(seed)-set(fillers[:2]))|{'a+a','b+b'})}
    # Independently use the existing parser/body audit; no complete source/body entry.
    codec_spec=importlib.util.spec_from_file_location('atomic_proof_codec',LIT/'stacking-structured-v1/codec.py')
    codec=importlib.util.module_from_spec(codec_spec);codec_spec.loader.exec_module(codec)
    nodes=codec.extract({**{'o'+pid:text for pid,text in original.items()},**{'r'+pid:text for pid,text in renamed.items()}})
    banned={body for row in nodes.values() for body in row['bodies']}
    assert all(not set(words)&banned for words in dictionaries.values())
    rows={'seed':score(original,seed),'rename_only':score(renamed,seed),
          'label_only':score(original,dictionaries['label']),
          'label_atomic':score(renamed,dictionaries['label']),
          'context_without_label_only':score(original,dictionaries['context_without_label']),
          'rename_plus_context_without_label':score(renamed,dictionaries['context_without_label']),
          'context_entries_only':score(original,dictionaries['context']),
          'context_atomic':score(renamed,dictionaries['context']),
          'literal_two_entry_control':score(original,dictionaries['literal_control'])}
    script="const vm=require('node:vm'),fs=require('node:fs');const pairs=JSON.parse(fs.readFileSync(0,'utf8'));for(const [a,b] of pairs){for(const x of [-3,0,2,10]){const one=vm.runInNewContext(a+';solve('+x+')'),two=vm.runInNewContext(b+';solve('+x+')');if(one!==two)throw Error('synthetic mismatch')}}process.stdout.write('ok')"
    got=subprocess.run(['node','-e',script],input=json.dumps([[original[p],renamed[p]] for p in original]),text=True,capture_output=True,check=True)
    assert got.stdout=='ok'
    return {'fixture':'eight invented safe bindings; two owners per original name; all dictionaries exactly256',
            'synthetic_execution_checks':32,'rows':rows,
            'subset_grid_complete':True,
            'limitations':['All eight combinations of rename/no-rename and the four entry subsets are scored. The context entry alone with renaming already lowers N; both entries are not jointly necessary.',
                           'The two-entry literal control is specified, not a globally optimal literal search.',
                           'Label-only atomic gain is C reclassification at unchanged N and package; not successor evidence.',
                           'This proves local admission reachability, not that D10 is trapped or that the corpus will improve.']}


if __name__=='__main__':print(json.dumps(proof(),sort_keys=True,indent=2))
