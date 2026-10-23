"""Explicit frozen utility imports; no input files are opened at import."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent;LIT=HERE.parent

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

dual=module('length_sensitive_fraction_encoder',LIT/'fraction-capacity-v1/dual.py')
analyze=dual.analyze
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write(path,value):
    path=Path(path);tmp=path.with_name(path.name+'.tmp')
    with tmp.open('w') as f:
        json.dump(value,f,indent=2,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)

def measure(texts,vocab,folder,decoder_bytes):
    """Production exact min-F encoder/packet writer; report replays independently."""
    folder.mkdir();write(folder/'dictionary.json',vocab);db=analyze.dictionary_bytes(vocab)
    (folder/'dictionary.bin').write_bytes(db);(folder/'packets').mkdir();rows={}
    for pid,text in sorted(texts.items()):
        value,seq=dual.encode_objective(text,vocab);packet=analyze.encode(vocab,seq,8)
        assert analyze.decode(db,packet)==text
        chars=sum(len(vocab[i])==1 for i in seq)
        rows[pid]={'source_sha256':analyze.sha(text.encode()),'selections':len(seq),'actions':len(seq)+1,'characters':chars,
            'objective':value,'packet_bytes':len(packet),'packet_sha256':analyze.sha(packet),
            'one_program_package_bytes':len(db)+len(packet),'one_program_with_decoder':len(db)+len(packet)+decoder_bytes}
        assert value==10*chars-len(seq);(folder/'packets'/f'{pid}.bin').write_bytes(packet)
    n=sum(r['selections'] for r in rows.values());chars=sum(r['characters'] for r in rows.values());package=len(db)+sum(r['packet_bytes'] for r in rows.values())
    supports=[sum(word in text for text in texts.values()) for word in vocab];assert all(supports)
    return {'per_problem':rows,'selections':analyze.distribution([r['selections'] for r in rows.values()]),
            'actions':analyze.distribution([r['actions'] for r in rows.values()]),'characters':chars,'character_fraction':chars/n,
            'objective':10*chars-n,'entries':len(vocab),'character_entries':sum(len(s)==1 for s in vocab),
            'dictionary_sha256':sha(folder/'dictionary.json'),'dictionary_bytes':len(db),'package_bytes':package,
            'package_with_decoder_sources':package+decoder_bytes,'amortized_package_bytes':package/len(rows),
            'framing_bytes':41*len(rows),'payload_bits':8*n,'padding_bits':0,'one_owner_entries':sum(n==1 for n in supports),
            'maximum_entry_length':max(map(len,vocab)),'semantic_reuse_audit':'not_performed_relaxation_witness_only'}
