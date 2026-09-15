"""Independent decoded-prefix reconstruction of native feature-validity boundaries."""
from pathlib import Path
import json,struct,hashlib
root=Path.cwd();out=root/'results/fx2_residual_features250k_v3';native=out/'work/native'
d=json.load(open(out/'decision.json'));assert d['status']=='passed'
body=(root/'results/fx2_weight_native_transfer250k_q0_v1/work/native/opening.stored').read_bytes()[10:]
archive=(native/'encode.arc').read_bytes()
vocab=[v for v in range(256) if archive[14+v//8]&(1<<(v%8))]
assert len(vocab)==205;index={v:i for i,v in enumerate(vocab)}
separator=bytes([8,8,0x25,0xac,0x65,0x27,5,8,8,8,8,0x25,0xac,0x68,0x27])
records=list(struct.iter_unpack('<QHBB',(native/'encode.features').read_bytes()))
assert len(records)==len(body)*8
history=bytearray(15);local=0;valid=False;missing=[]
for i,value in enumerate(body):
 # Compare BEFORE consuming the current byte. No current truth in validity.
 for j in range(8):
  packed,count,flags,truth=records[8*i+j]
  assert bool(flags&8)==valid and flags&7==j
  if not valid:assert packed==0
 if not valid:missing.append(i)
 history=history[1:]+bytes([index[value]]);local+=1
 if history==separator or local>=1<<17:local=0;valid=False
 else:valid=True
result=dict(schema='gamma.enwiki9.feature-validity-independent.v1',modeled_bytes=len(body),bit_events=len(records),vocabulary_size=len(vocab),validity_from_decoded_prefix_only=True,all_validity_bits_match=True,missing_feature_byte_coordinates=missing,missing_feature_bytes=len(missing),feature_trace_sha256=hashlib.sha256((native/'encode.features').read_bytes()).hexdigest(),original_predictor_source_sha256=hashlib.sha256((root/'results/fx2_cmix_transformer_static_vocab_fixture50051_q0_v1/work/src/predictor.cpp').read_bytes()).hexdigest(),objective_credit_bytes=0)
closure=out/'closure';closure.mkdir(exist_ok=True)
(closure/'feature_validity.json').write_text(json.dumps(result,indent=2)+'\n')
(closure/'feature_validity_check.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps({k:v for k,v in result.items() if k!='missing_feature_byte_coordinates'}))
