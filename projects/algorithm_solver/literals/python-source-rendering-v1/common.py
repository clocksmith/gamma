"""Pinned metadata and supplied-artifact helpers; no import-time corpus access."""
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import engine
import render

HERE=Path(__file__).resolve().parent;LIT=HERE.parent
analyze=engine.parent.analyze;tail=engine.parent.tail
write=engine.parent.write_atomic
sha=lambda raw:hashlib.sha256(raw).hexdigest()

def require_assertions():
    if not __debug__ or sys.flags.optimize or 'PYTHONOPTIMIZE' in os.environ:
        raise RuntimeError('Optimized Python/PYTHONOPTIMIZE forbidden')
require_assertions()

def checked(spec):
    raw=Path(spec['file']).read_bytes();assert sha(raw)==spec['sha256'],'pinned artifact mismatch'
    return json.loads(raw)

def contract():
    c=json.loads((HERE/'contract.json').read_text())
    assert c['execution_authorized'] is True and c['schema']=='gamma.python-source-rendering.v1'
    return c

def identity(width,arm):
    assert width in (7,8) and arm in engine.ARMS
    return f'w{width}/{arm}'

def finite_seconds(value,maximum=None):
    assert type(value) in (int,float) and math.isfinite(value) and value>=0,'invalid timing receipt'
    if maximum is not None:assert value<=maximum,'timing receipt exceeds frozen bound'
    return value

def renderer_runtime_files():
    paths=(Path(sys.executable).resolve(),Path(render.ast.__file__).resolve(),Path(render.tokenize.__file__).resolve())
    return {str(path):sha(path.read_bytes()) for path in paths}

def verify_runtime_files(c):
    for path,h in c['runtime_files'].items():assert sha(Path(path).read_bytes())==h,path
    assert all(c['runtime_files'].get(path)==h for path,h in renderer_runtime_files().items()),'renderer runtime pin missing or changed'

def verify(c):
    require_assertions()
    assert str(Path(sys.executable).resolve())==c['python_bin']
    assert len(c['partition']['dev_fit'])==27 and len(c['partition']['dev_val'])==9
    assert len(set(c['partition']['dev_fit']+c['partition']['dev_val']))==36
    assert set(c['entries'])==set(map(str,c['partition']['dev_fit']+c['partition']['dev_val']))
    for rel,h in c['code_hashes'].items():assert sha((LIT/rel).read_bytes())==h,rel
    verify_runtime_files(c)
    old=checked(c['parent_contract']);receipt=checked(c['qualification'])
    assert old['partition']==c['partition'] and old['sources']==c['sources']
    assert receipt['contract_sha256']==c['parent_contract']['sha256']
    assert c['inputs']==checked(c['anchor_pin_contract'])['inputs']
    assert set(c['decoder_source_files'])=={'literals.py','pass2/working/bitpack.py'}
    for rel,d in c['decoder_source_files'].items():
        raw=(LIT/rel).read_bytes();assert sha(raw)==d['sha256'] and len(raw)==d['bytes']
    assert c['decoder_source_bytes']==sum(d['bytes'] for d in c['decoder_source_files'].values())

def texts_checked(c,width,fit_only=False,original=False):
    assert not (fit_only and original)
    row=c['inputs'][str(width)]['fit' if fit_only else 'original_sources' if original else 'sources']
    texts=checked(row)
    ids=c['partition']['dev_fit'] if fit_only else c['partition']['dev_fit']+c['partition']['dev_val']
    assert set(texts)==set(map(str,ids))
    prior=checked(c['qualification'])
    arm=next(a for a in prior['arms'] if a['width']==width and a['arm']==('control' if original else 'scope_joint'))
    for pid,text in texts.items():
        assert arm['qualification'][pid]['passed'] and sha(text.encode())==arm['per_problem'][pid]['source_sha256']
    return texts

def authority(c,width,original=False):
    prior=checked(c['qualification'])
    return next(a for a in prior['arms'] if a['width']==width and a['arm']==('control' if original else 'scope_joint'))

def variants_for(arm,texts,groups):
    return groups if arm in ('S','J') else {pid:engine.normalized(text,[text]) for pid,text in texts.items()}

def evaluate(texts,vocab,width,c,menus):
    entries={pid:c['entries'][pid] for pid in texts}
    groups={pid:engine.normalized(texts[pid],m['candidates'].values()) for pid,m in menus.items()}
    ban=engine.parent.banned(groups,entries)
    rows,illegal=tail.evaluate_output(texts,vocab,width,ban)
    db=analyze.dictionary_bytes(vocab)
    return {'width':width,'entries':len(vocab),'dictionary_bytes':len(db),'per_problem':rows,
            'illegal_entry_sha256':illegal,'fit':tail.aggregate(rows,c['partition']['dev_fit'],len(db)),
            'validation':tail.aggregate(rows,c['partition']['dev_val'],len(db))}

def save_packets(folder,texts,vocab,width):
    db=analyze.dictionary_bytes(vocab);(folder/'dictionary.bin').write_bytes(db)
    packets=folder/'packets';packets.mkdir()
    for pid,text in texts.items():
        try:sequence=analyze.shortest_encode(text,vocab)
        except ValueError:continue
        packet=analyze.encode(vocab,sequence,width)
        assert analyze.decode(db,packet)==text
        (packets/f'{pid}.bin').write_bytes(packet)

def seal_files(folder,names):return {name:sha((folder/name).read_bytes()) for name in names}

def check_files(folder,seal):
    for name,h in seal.items():assert sha((folder/name).read_bytes())==h
