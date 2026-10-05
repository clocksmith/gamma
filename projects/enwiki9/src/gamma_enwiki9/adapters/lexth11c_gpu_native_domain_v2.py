"""Isolated GPU runtime diagnostic, with native values and reference backward."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct

from gamma_enwiki9.adapters.lexth11c_build import sandbox, write
from gamma_enwiki9.evidence.artifacts import fingerprint
from gamma_enwiki9.execution.commands import CommandExecutor, PhaseLimits
from gamma_enwiki9.execution.memory import CgroupMemoryGuard
from gamma_enwiki9.types import BuildProfile, ExecutionContext, ResourceBudget

def inner(root,output,raw):
    import torch
    import numpy as np
    import types
    from .lexth11c_gpu_reference import load
    from .fx2_native_forward import attach_native_values
    torch.set_num_threads(2)
    torch.set_float32_matmul_precision("highest")
    visibility={'torch':torch.__version__,'hip':torch.version.hip,
        'cuda_available':torch.cuda.is_available(),'cuda_count':torch.cuda.device_count(),'target_device':'cuda'}
    print(json.dumps(visibility),flush=True)
    if not visibility['cuda_available']:raise RuntimeError('GPU unavailable')
    model,manifest,control=load(root,raw,output/'reference-package','cuda')
    # Integer-domain GEMM preserves the donor quantizer and scale order.
    # Norms, recurrence, quantization arithmetic and optimizer masters stay FP32.
    patched=0
    for module in model.modules():
        if type(module).__name__=='CastedLinear':
            def forward(self,x,initialize_scales):
                original=x
                if self.quantize_activation is not None:
                    x=self.quantize_activation(x,initialize_scales_steps=initialize_scales.activation_steps,return_ints=False)
                weight=self.weight
                if self.quantize_weight is not None:
                    weight=self.quantize_weight(weight,initialize_scales_steps=initialize_scales.weight_steps,return_ints=False)
                surrogate=torch.nn.functional.linear(x.float(),weight.float())
                if self.quantize_weight is not None and self.quantize_activation is not None:
                    quant=self.quantize_weight
                    scale=original.float().abs().amax(-1,keepdim=True).clamp_min(1e-12)/127.0
                    ai=(original.float()/scale).round().clamp(-128,127)
                    q=quant.indices(self.weight)
                    wi=q.float() if quant.small else quant.levels[q+7]/0.25
                    fold=quant.scale.to(torch.bfloat16).float()*(1.0 if quant.small else 0.25)
                    actual=(torch.nn.functional.linear(ai,wi)*fold)*scale
                    y=attach_native_values(surrogate,actual.detach())
                else:y=surrogate
                return y if self.bias is None else y+self.bias.float()
            module.forward=types.MethodType(forward,module);patched+=1
    tokens=torch.arange(8,device='cuda').long().reshape(1,8)
    priors=torch.full((1,8,205),1/205,dtype=torch.float16,device='cuda').float()
    torch.cuda.reset_peak_memory_stats()
    logits=model.compute_logits(tokens,priors,None)
    actual=torch.from_numpy(np.fromfile(output/'work/native.f32',dtype=np.float32).reshape(8,410)[:,:205].copy()).to('cuda').unsqueeze(0)
    reference_error=float((logits.detach()-actual).abs().max())
    probability_error=float((logits.detach().softmax(-1)-actual.softmax(-1)).abs().max())
    # Exact native values enter loss; only the Jacobian comes from the GPU reference.
    native_logits=attach_native_values(logits,actual)
    if not torch.equal(native_logits,actual):raise ValueError('native forward value mismatch')
    loss=torch.nn.functional.cross_entropy(native_logits.reshape(-1,205),(tokens.flatten()+1)%205)
    optimizer=torch.optim.AdamW(model.parameters(),lr=1e-5,betas=(0.9,0.95),eps=1e-8,weight_decay=0)
    optimizer.zero_grad(set_to_none=True);loss.backward()
    gradients=[p.grad for p in model.parameters() if p.grad is not None]
    finite=all(bool(g.isfinite().all()) for g in gradients)
    if not finite or not gradients:raise ValueError('gradient failure')
    parameter=model.unembedding.weight;before=parameter.detach().clone()
    torch.nn.utils.clip_grad_norm_(model.parameters(),1.0);optimizer.step();torch.cuda.synchronize()
    changed=not torch.equal(before,parameter.detach())
    if not changed or not all(bool(p.isfinite().all()) for p in model.parameters()):raise ValueError('optimizer failure')
    maps=sorted({line.split()[-1] for line in Path('/proc/self/maps').read_text().splitlines()
        if len(line.split())>=6 and ('rocm' in line.split()[-1] or '/torch/lib/' in line.split()[-1])})
    userspace=[fingerprint(Path(p),root) for p in maps if Path(p).is_file()]
    result={'schema':'gamma.enwiki9.donor-gpu-operations.v1','status':'operations_pass',
        'visibility':visibility,'device_name':torch.cuda.get_device_name(),'gfx':torch.cuda.get_device_properties(0).gcnArchName,
        'precision':'FP32 integer-domain GEMM for exact W4/W8/A8 sums, original row-then-token scale order; FP32 recurrence,norm,masters and AdamW state',
        'linear_sites':patched,'loaded_released_tensor_count':435,'unchanged_index_export_control':control,
        'native_forward_values_exact':True,'reference_max_logit_error':reference_error,'reference_max_probability_error':probability_error,
        'native_reference_probability_gate':probability_error<=1e-5,
        'backward':'Approximate whole-reference Jacobian; not an exact derivative of native kernels',
        'gradient_tensors':len(gradients),'finite_gradients':finite,'optimizer_parameter_changed':changed,
        'loss_nats':float(loss.detach()),'gpu_peak_allocated_bytes':torch.cuda.max_memory_allocated(),
        'gpu_peak_reserved_bytes':torch.cuda.max_memory_reserved(),'loaded_userspace':userspace,
        'reference_source_manifest':manifest,'host_matrix_os_match':False,
        'full_training_ready':False,'training_blockers':['Full causal deployed PPMD inputs and storage alignment','Fresh native-forward/export validation for updated checkpoints','Frozen resumed-training source and assigned full-data compute'],
        'qualification':False,'objective_credit_bytes':0}
    write(output/'operations.json',result);print(json.dumps(result),flush=True)

def outer(root,output,experiment,raw):
    exp=json.loads(experiment.read_bytes())
    bound={'path':experiment.relative_to(root).as_posix(),'sha256':'sha256:'+hashlib.sha256(experiment.read_bytes()).hexdigest()}
    if json.loads(os.environ['GAMMA_ENWIKI9_EXPERIMENT_JSON'])!=bound:raise ValueError('lab binding differs')
    for row in exp['inputs']:
        if fingerprint(root/row['path'],root)['sha256']!=row['sha256'].removeprefix('sha256:'):raise ValueError('input differs: '+row['path'])
    caps={'cpus':[7,8],'memory_bytes':12884901888,'scratch_bytes':3000000000,'wall_seconds':3600}
    env={'PATH':'/usr/bin:/bin','LC_ALL':'C','LD_LIBRARY_PATH':str(root/'external/lexth11c-campaign/gpu-rocm/opt/rocm-7.2.1/lib'),
        'HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1','TOKENIZERS_PARALLELISM':'false',
        'MIOPEN_USER_DB_PATH':str(output/'miopen'),'TORCHINDUCTOR_CACHE_DIR':str(output/'torch-cache')}
    ctx=ExecutionContext(exp['experimentId'],root,output,
        ResourceBudget(tuple(caps['cpus']),caps['memory_bytes'],caps['scratch_bytes'],caps['wall_seconds']),BuildProfile((),()),tuple(env.items()))
    work=output/'work';work.mkdir()
    (work/'rows').write_bytes(bytes(v for i in range(8) for v in (i,1 if i==0 else 0)))
    (work/'priors').write_bytes(struct.pack('<e',1/205)*205*8)
    source='/entry/cpp_infer/src/'
    units=[source+'weights_io.cpp',source+'weights_io_compressed.cpp']
    units +=[source+'opt/'+n+'.cpp' for n in ['qmat_dense','qmat_sparse','qmat_cpu','attn','kda','glue','arena_build','model_opt']]
    build=['clang++-17','-O3','-std=c++17','-march=x86-64-v3','-mrecip=none','-fno-math-errno',
        '-DQMAT_CODEBOOK=1','-DQMAT_WMAX=21','-DQMAT_SMALL_W8=1','-DTF_ACTQ_DYN=1',
        '-I/entry','/harness.cpp',*units,'-o','/work/native-forward']
    command=sandbox(root,work,build);index=command.index('--')
    command[index:index]=['--ro-bind',str(root/'tests/fx2_native_forward.cpp'),'/harness.cpp']
    phases=[];ok=True
    with CgroupMemoryGuard.current(caps['memory_bytes']) as guard:
        executor=CommandExecutor(ctx,resident_guard=guard)
        for name,cmd in [('native-build',command),('native-forward',sandbox(root,work,['./native-forward','/entry/models/lex_h1_run11.tfwc2','/work/rows','/work/priors','/work/native.f32']))]:
            outcome,rec=executor.run(name,cmd,PhaseLimits(600,600,68719476736,caps['scratch_bytes']));phases.append(rec)
            ok=outcome.classification=='completed'
            if not ok:break
        if ok:
            cmd=[str(root/'external/lexth11c-campaign/gpu-env/bin/python'),str(root/next(r['path'] for r in exp['inputs'] if r['id']=='runner')),
                '--inner','--root',str(root),'--output',str(output),'--raw',str(raw)]
            outcome,rec=executor.run('gpu-operations',cmd,PhaseLimits(600,600,68719476736,caps['scratch_bytes']));phases.append(rec);ok=outcome.classification=='completed'
    result={'schema':'gamma.enwiki9.gpu-probe-result.v1','experiment':bound,'status':'operations_pass' if ok else 'failed',
        'phases':phases,'qualification':False,'objective_credit_bytes':0,
        'operations':fingerprint(output/'operations.json',root) if (output/'operations.json').exists() else None}
    write(output/'result.json',result);print(json.dumps(result),flush=True);return 0 if ok else 1

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--inner',action='store_true')
    for n in ['root','output','raw']:p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--experiment',type=Path)
    a=p.parse_args()
    if a.inner:inner(a.root.resolve(),a.output.resolve(),a.raw.resolve());return 0
    return outer(a.root.resolve(),a.output.resolve(),a.experiment.resolve(),a.raw.resolve())
