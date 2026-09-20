"""Bounded fixed-checkpoint attribution; this module never constructs an optimizer."""
from __future__ import annotations
import argparse
import hashlib
import importlib
import json
from pathlib import Path
import subprocess

from .fx2_training_capture import source_members, validate_rows
from .fx2_numeric_native import instrument
from .fx2_numeric_reference import Reference, read_trace, read_weights, first_difference, differences, loss_bits
from .fx2_training_reference import materialize, load_package, load_model
from .fx2_weight_training import export_entries


def write(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2);f.write('\n')


def identity(path):
    with path.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
    return {'bytes':path.stat().st_size,'sha256':sha}


def plain_replay(model,tokens,markers,priors):
    import numpy as np
    import torch
    result=np.zeros((len(tokens),410),dtype='<f4');start=0
    model.eval()
    with torch.no_grad():
        while start<len(tokens):
            if markers[start]==2:start+=1;continue
            if markers[start]!=1:raise ValueError('missing real reset')
            end=start+1
            while end<len(tokens) and markers[end]!=2:end+=1
            logits=model.compute_logits(torch.from_numpy(tokens[start:end].astype(np.int64)).reshape(1,-1),
                torch.from_numpy(priors[start:end].astype(np.float32)).unsqueeze(0),torch.tensor([[0,end-start]],dtype=torch.int32))[0]
            result[start:end,:205]=logits.numpy();result[start:end,205:]=logits.softmax(-1).numpy();start=end+1
    return result


def run(root:Path,output:Path,plan:dict):
    import numpy as np
    import torch
    torch.set_num_threads(1);torch.use_deterministic_algorithms(True)
    output.mkdir(parents=True,exist_ok=False)
    builds={};commands=[];adaptation=None
    for kind in ('base','observed'):
        native=output/kind;native.mkdir()
        if kind=='base':members=source_members(root/plan['native_source_zip'])
        else:members,adaptation=instrument(root/plan['native_source_zip'])
        for name,data in members.items():
            path=native/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        infer=native/'cpp_infer/src';binary=native/'numeric-replay'
        sources=[infer/'weights_io.cpp',infer/'weights_io_compressed.cpp',*[infer/'opt'/(s+'.cpp') for s in
                ('qmat_dense','qmat_sparse','attn','kda','glue','arena_build','model_opt')]]
        command=['/usr/bin/g++','-std=c++17','-O3','-march=x86-64-v3','-mrecip=none','-fno-math-errno',
                 '-I',str(native),'-I',str(root/'tests'),str(root/'tests/fx2_numeric_replay.cpp'),*map(str,sources),'-o',str(binary)]
        subprocess.run(command,check=True,timeout=120);commands.append(command);builds[kind]=binary
    result={'schema':'gamma.enwiki9.fx2-numeric-attribution.v1','plan':plan,'runtime':{'torch':torch.__version__,'device':'cpu','threads':1},
            'native_adaptation':adaptation,'build_commands':commands,'native_binaries':{k:identity(v) for k,v in builds.items()},
            'fixtures':{},'weights':{},'objective_credit_bytes':0,'training_performed':False,'full_corpus_score_bytes':None,
            'trace_scope':'All quantized linear inputs and integer dots, vanilla Q/K/V quantizers, normalized embedding and block boundaries within first 64 input rows; not complete parent state.',
            'accumulator_scope':'Native integer dots are queried from the same arena. Reference integer dots are reconstructed from its actual quantized inputs/weights; Torch itself accumulates dequantized FP32 products.',
            'intervention_scope':'Diagnostic-only substitutions: at most 8 successive first-integer scalar changes and 3 first-value full-vector changes at one row/operation per checkpoint/fixture. No deployment or training.'}
    for fixture in plan['fixtures']:
        folder=output/fixture;folder.mkdir()
        if fixture=='synthetic':
            tokens=np.arange(8,dtype=np.uint8);markers=np.zeros(8,dtype=np.uint8);markers[0]=1
            priors=np.full((8,205),0x1cff,dtype='<u2').view('<f2')
        elif fixture=='native_prefix2048':
            path=root/plan['captured_tokens'];raw=path.read_bytes()
            validate_rows(raw,(root/plan['captured_priors']).stat().st_size)
            tokens=np.frombuffer(raw[:4096:2],dtype=np.uint8).copy();markers=np.frombuffer(raw[1:4096:2],dtype=np.uint8).copy()
            with (root/plan['captured_priors']).open('rb') as f:priors=np.frombuffer(f.read(2048*410),dtype='<f2').copy().reshape(2048,205)
            if len(tokens)!=2048 or not np.isfinite(priors).all():raise ValueError('native fixture differs')
        else:raise ValueError('unknown fixed fixture')
        rows=np.stack((tokens,markers),axis=1);rows.tofile(folder/'tokens-markers.bin');priors.tofile(folder/'priors.f16')
        item={'rows':len(tokens),'piece_end_rows':np.flatnonzero(markers==2).tolist(),'reset_rows':np.flatnonzero(markers==1).tolist(),
              'inputs':{p.name:identity(p) for p in folder.iterdir()},'arms':{}}
        for arm,paths in plan['checkpoints'].items():
            target=folder/arm;target.mkdir();packed=root/paths['packed'];checkpoint=root/paths['checkpoint']
            for kind,binary in builds.items():
                command=[str(binary),str(packed),str(folder/'tokens-markers.bin'),str(folder/'priors.f16'),str(target/(kind+'.f32')),
                         str(target/'native.trace') if kind=='observed' else '-',str(plan['trace_rows']),str(target/(kind+'.weights'))]
                subprocess.run(command,check=True,timeout=120)
            if (target/'base.f32').read_bytes()!=(target/'observed.f32').read_bytes():raise ValueError('native observation changed prediction')
            if (target/'base.weights').read_bytes()!=(target/'observed.weights').read_bytes():raise ValueError('native decoded weights differ')
            native=np.fromfile(target/'base.f32',dtype='<f4').reshape(len(tokens),410)
            traced,order=read_trace(target/'native.trace')
            refdir=target/'reference';materialize(root/plan['upstream'],refdir);package=load_package(refdir)
            model=load_model(package,checkpoint);template=importlib.import_module(package+'.weights_compress').read_tensor_file_v2(str(packed))
            native_weights=read_weights(target/'base.weights');exported={n:(k,a) for n,k,a in export_entries(model,template,package)}
            if native_weights.keys()!=template.keys() or exported.keys()!=template.keys():raise ValueError('weight inventories differ')
            weight_rows=[]
            for name,(kind,array) in template.items():
                nk,na=native_weights[name];ek,ea=exported[name]
                if nk!=kind or ek!=kind or na.dtype!=array.dtype or na.shape!=array.shape or na.tobytes()!=array.tobytes() or ea.tobytes()!=array.tobytes():raise ValueError('decoded/exported tensor mismatch: '+name)
                weight_rows.append({'name':name,'kind':kind,'shape':list(array.shape),'sha256':hashlib.sha256(array.tobytes()).hexdigest()})
            write(target/'decoded-tensors.json',weight_rows)
            before={n:hashlib.sha256(v.detach().numpy().tobytes()).hexdigest() for n,v in model.state_dict().items()}
            plain=plain_replay(model,tokens,markers,priors);plain.tofile(target/'reference-plain.f32')
            reference=Reference(package,model,template,plan['trace_rows']);logits,prob,captured=reference.replay(tokens,markers,priors)
            if not np.array_equal(logits.view('<u4'),plain[:,:205].copy().view('<u4')) or not np.array_equal(prob.view('<u4'),plain[:,205:].copy().view('<u4')):raise ValueError('reference observation changed prediction')
            nl,nt=loss_bits(native[:,205:],tokens,markers);rl,rt=loss_bits(prob,tokens,markers)
            nt.astype('<f4').tofile(target/'native-truth.f32');rt.astype('<f4').tofile(target/'reference-truth.f32')
            # Keep baseline corresponding reference records in the same explicit geometry.
            import struct
            with (target/'reference.trace').open('xb') as f:
                for row,key in order:
                    value=captured[row,key].astype('<f4');encoded=key.encode()
                    f.write(struct.pack('<III',row,len(encoded),value.size));f.write(encoded);f.write(value.tobytes())
            summary={'native_loss':nl,'reference_loss':rl,'loss_gap_bits':nl['bits']-rl['bits'],
                     'native_observation_bitwise_equal':True,'reference_observation_bitwise_equal':True,'decoded_tensors_equal':len(template),
                     'first_compared_bit_difference':first_difference(traced,captured,order),
                     'first_integer_difference':first_difference(traced,captured,order,suffix='.integer'),
                     'baseline_differences':differences(traced,captured,order),'interventions':{}}
            for family,maximum in [('value',plan['value_interventions']),('integer',plan['integer_interventions'])]:
                interventions=[];current=captured;steps=[]
                # Value interventions cover observed module outputs and normalized embeddings.
                selected=[pair for pair in order if pair[1]=='embedding.normalized' or (pair[1].endswith('.output') and not pair[1].startswith('blocks.')) or
                          (pair[1].endswith('.output') and pair[1].count('.')>2)] if family=='value' else order
                for step in range(maximum):
                    delta=first_difference(traced,current,selected,suffix='.integer' if family=='integer' else None)
                    if delta is None:break
                    edit={k:delta[k] for k in ('row','key','coordinate','native')}
                    if family=='value':edit['values']=traced[delta['row'],delta['key']].tolist()
                    interventions.append(edit)
                    li,pi,current=reference.replay(tokens,markers,priors,interventions)
                    loss,truth=loss_bits(pi,tokens,markers)
                    pi.astype('<f4').tofile(target/(f'{family}-{step+1}.probabilities.f32'))
                    residual=float(np.max(np.abs(li-native[:,:205])))
                    steps.append({'substitution':delta,'substituted_elements':len(edit.get('values',[edit['native']])),'reference_loss_after':loss,'remaining_logit_max':residual,
                                  'next_compared_difference':first_difference(traced,current,selected,suffix='.integer' if family=='integer' else None),
                                  'trace_differences':differences(traced,current,order)})
                summary['interventions'][family]={'steps':steps,'stopped_at_declared_limit':len(steps)==maximum,
                                                  'remaining_compared_difference':first_difference(traced,current,selected,suffix='.integer' if family=='integer' else None)}
            after={n:hashlib.sha256(v.detach().numpy().tobytes()).hexdigest() for n,v in model.state_dict().items()}
            if after!=before:raise ValueError('checkpoint state changed during evaluation')
            summary['parameters_unchanged']=True;write(target/'comparison.json',summary);item['arms'][arm]=summary
            # Decoded full tensors are independently verified, then retained by identity manifest;
            # exact packed inputs already live in the frozen closure. Avoid duplicated RoPE buffers.
            (target/'base.weights').unlink();(target/'observed.weights').unlink()
        p,e=item['arms']['P'],item['arms']['E']
        dr=e['reference_loss']['bits']-p['reference_loss']['bits'];dn=e['native_loss']['bits']-p['native_loss']['bits']
        item['delta_reference_bits']=dr;item['delta_native_bits']=dn;item['delta_mismatch_bits']=dn-dr
        result['fixtures'][fixture]=item
        print(json.dumps({'fixture':fixture,'delta_reference_bits':dr,'delta_native_bits':dn,'delta_mismatch_bits':dn-dr}),flush=True)
    result['comparison_complete']=True;result['promotion_authorized']=False
    write(output/'comparison.json',result)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--plan',type=Path,required=True)
    args=parser.parse_args();run(args.root.resolve(),args.output.resolve(),json.loads(args.plan.read_bytes()))
