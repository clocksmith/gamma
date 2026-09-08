"""Synthetic evidence for a stale slot at an encoded text-close boundary."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import sys

ROOT=Path(__file__).resolve().parents[2]
os.sched_setaffinity(0,{3})
resource.setrlimit(resource.RLIMIT_AS,(536870912,)*2)
resource.setrlimit(resource.RLIMIT_CPU,(30,)*2)
path=ROOT/'programs/opcode_wiki_slot_v1/program.py'
assert hashlib.sha256(path.read_bytes()).hexdigest()=='93514bf36ed453e84ad211bfb6121a56363b90c74c6c327f581e86f952341bce'
spec=importlib.util.spec_from_file_location('sealed_slot_codec',path)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
raw=b'<text xml:space="preserve">==References==\n</text><title>Next</title><text xml:space="preserve">plain'
namespaces={arm:module.namespace(arm) for arm in ('P','D')}
modeled=namespaces['P']['oe'](raw)
close=modeled.index(b'\0\x02')
states={}
for arm,ns in namespaces.items():
    ns['_limit']=len(modeled);states[arm]=ns['GST']()
rows=[]
for position,byte in enumerate(modeled):
    for state in states.values():state.up(byte)
    if position in (close-1,close,close+1,len(modeled)-1):
        rows.append(dict(position=position,modeled_byte=byte,
            states={a:dict(slot=s.slot,field=s.f,pending=s.field.pending) for a,s in states.items()}))
assert [r['states']['P']['slot'] for r in rows]==[9,9,9,9]
assert [r['states']['D']['slot'] for r in rows]==[9,9,0,0]
receipt=dict(schema='gamma.enwiki9.opcode-slot-reset-diagnostic.v1',synthetic_only=True,
    raw_hex=raw.hex(),modeled_hex=modeled.hex(),rows=rows,
    source=dict(path=str(path.relative_to(ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest()),
    probe_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    compressed_bytes_measured=False,codec_source_changed=False,
    conclusion='The compact parent retains slot9 across this encoded text close and into the next text. Raw reconstructed state resets only after the complete opcode. This proves the demonstrated state mismatch, not that reset explains the measured57-byte archive saving.',
    next_experiment='Starting from the compact parent, change only slot reset on a completed opcode2. Keep raw semantic-slot discovery disabled. Compare unchanged parent, unused bookkeeping and reset-only treatment with exact archives and package accounting.',
    bounds=dict(cpu=3,threads=1,address_space_bytes=536870912,cpu_seconds=30))
out=Path(sys.argv[1]);out.parent.mkdir(parents=True,exist_ok=True)
with out.open('x') as stream:json.dump(receipt,stream,indent=2,sort_keys=True);stream.write('\n')
print(json.dumps(rows))
