"""Sparse source-to-RDRR scalar checks and exact text architecture checks; no GPU."""
import argparse
import collections
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import time

p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--model',required=True);p.add_argument('--output',required=True);a=p.parse_args()
source=Path(a.source);model=Path(a.model);started=time.monotonic()
sha=lambda b:hashlib.sha256(b).hexdigest()
manifest_bytes=(model/'manifest.json').read_bytes();manifest=json.loads(manifest_bytes)
config_bytes=(source/'config.json').read_bytes();config=json.loads(config_bytes)['text_config']
index_bytes=(source/'model.safetensors.index.json').read_bytes();index=json.loads(index_bytes)['weight_map']
if manifest['artifactIdentity']['sourceRevision']!='c202236235762e1c871ad0ccb60c8ee5ba337b9a':raise ValueError('Wrong source revision')
checks={k:manifest['architecture'][k]==config[v] for k,v in {'numLayers':'num_hidden_layers','hiddenSize':'hidden_size','intermediateSize':'intermediate_size','numAttentionHeads':'num_attention_heads','numKeyValueHeads':'num_key_value_heads','headDim':'head_dim','vocabSize':'vocab_size','maxSeqLen':'max_position_embeddings','linearNumKeyHeads':'linear_num_key_heads','linearNumValueHeads':'linear_num_value_heads','linearKeyHeadDim':'linear_key_head_dim','linearValueHeadDim':'linear_value_head_dim','linearConvKernelDim':'linear_conv_kernel_dim'}.items()}
checks['exactLayerTypes']=manifest['inference']['layerPattern']['layerTypes']==config['layer_types']
checks['sourceTextTensorsExactlyRetained']=set(manifest['tensors'])=={k for k in index if k.startswith('model.language_model.') or k=='lm_head.weight'}
checks['completeTextArtifact']=manifest['artifactIdentity']['artifactCompleteness']=='complete' and manifest['artifactIdentity']['modalitySet']==['text']
checks['f16WeightsF32Compute']=manifest['quantization']=='F16' and manifest['quantizationInfo']['compute']=='f32'
if not all(checks.values()):raise ValueError(f'Architecture mismatch: {checks}')
headers={};handles={};source_dtype_counts=collections.Counter();header_hashes={}
try:
 for filename in sorted(set(index.values())):
  h=open(source/filename,'rb');handles['source/'+filename]=h;n=struct.unpack('<Q',h.read(8))[0];b=h.read(n)
  headers[filename]=(8+n,json.loads(b));header_hashes[filename]=sha(b)
  for name,entry in headers[filename][1].items():
   if name!='__metadata__':source_dtype_counts[entry['dtype']]+=1
 def read_converted(t,offset,size):
  spans=t.get('spans',[{'shardIndex':t.get('shard'),'offset':t.get('offset',0),'size':t['size']}]);logical=0;remaining=size;result=b''
  for span in spans:
   if offset>=logical+span['size']:logical+=span['size'];continue
   within=max(0,offset-logical);count=min(remaining,span['size']-within)
   filename=manifest['shards'][span['shardIndex']]['filename'];key='converted/'+filename
   if key not in handles:handles[key]=open(model/filename,'rb')
   result+=os.pread(handles[key].fileno(),count,span['offset']+within);remaining-=count;offset+=count;logical+=span['size']
   if not remaining:break
  if len(result)!=size:raise ValueError('Truncated converted tensor')
  return result
 rows=[];count=0
 for name,t in manifest['tensors'].items():
  filename=index[name];base,header=headers[filename];entry=header[name];shape=entry['shape'];length=math.prod(shape)
  if t['shape']!=shape or t['dtype']!='F16' or t['size']!=length*2:raise ValueError(f'Shape/dtype/size mismatch: {name}')
  positions=sorted(set([*range(min(8,length)),*range(max(0,length-8),length),*(i*(length-1)//32 for i in range(33))]))
  fd=handles['source/'+filename].fileno();kind=entry['dtype'];width={'BF16':2,'F16':2,'F32':4}[kind];mismatches=[];samples=[]
  for i in positions:
   raw=os.pread(fd,width,base+entry['data_offsets'][0]+i*width)
   value=struct.unpack('<f',b'\0\0'+raw)[0] if kind=='BF16' else struct.unpack('<e' if kind=='F16' else '<f',raw)[0]
   expected=struct.pack('<e',value);actual=read_converted(t,i*2,2);observed=struct.unpack('<e',actual)[0]
   if not math.isfinite(value) or not math.isfinite(observed) or actual!=expected:mismatches.append({'index':i,'source':value,'converted':observed,'expectedHex':expected.hex(),'actualHex':actual.hex()})
   samples.append([i,value,observed]);count+=1
  rows.append({'name':name,'shape':shape,'sourceDtype':kind,'convertedDtype':t['dtype'],'sampleCount':len(positions),'samplesSha256':sha(json.dumps(samples,separators=(',',':')).encode()),'firstSamples':samples[:3],'mismatches':mismatches,'passed':not mismatches})
 if any(not r['passed'] for r in rows):raise ValueError(json.dumps([r for r in rows if not r['passed']])[:2000])
 if sha((model/'manifest.json').read_bytes())!=sha(manifest_bytes):raise ValueError('Manifest changed while verifying')
 result={'schema':'gamma.channel-gain-converted-source-sample-parity/v1','sourceRevision':manifest['artifactIdentity']['sourceRevision'],'manifestSha256':sha(manifest_bytes),'sourceConfigSha256':sha(config_bytes),'sourceIndexSha256':sha(index_bytes),'sourceHeaderSha256':header_hashes,'sourceAllTensorDtypeCounts':dict(source_dtype_counts),'architectureChecks':checks,'layerTypes':config['layer_types'],'tensorsChecked':len(rows),'scalarSamplesChecked':count,'method':'For every text tensor, first/last eight and 33 uniformly-spaced scalar positions; exact source-to-IEEE-f16 round-to-nearest-even byte agreement, source/target finite checks. Sparse reads only.','tensors':rows,'elapsedSeconds':time.monotonic()-started,'passed':True,'gpuExecuted':False,'inferenceExecuted':False}
 with Path(a.output).open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
 print(json.dumps({k:result[k] for k in ['passed','tensorsChecked','scalarSamplesChecked','elapsedSeconds','manifestSha256']}))
finally:
 for h in handles.values():h.close()
