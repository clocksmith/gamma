"""Released-weight import and full architecture GPU diagnostic.

The earlier authenticated FX2 architecture supplies a differentiable reference.
Lexth11c's nonuniform codebooks, small eight-bit tables and dynamic activation
quantization are imported explicitly. This does not recover run11's recipe.
Native forward remains authoritative; the reference Jacobian is approximate.
"""
from __future__ import annotations
import importlib
from pathlib import Path
import struct

from .fx2_training_reference import materialize, load_package

def read_raw(path):
    import numpy as np
    entries={}
    with Path(path).open('rb') as f:
        if f.read(8)!=b'FX2TFW01':raise ValueError('raw magic differs')
        count=struct.unpack('<I',f.read(4))[0]
        for _ in range(count):
            n=struct.unpack('<I',f.read(4))[0];name=f.read(n).decode()
            dtype=f.read(1)[0];nd=struct.unpack('<I',f.read(4))[0]
            shape=struct.unpack('<'+'I'*nd,f.read(4*nd))
            size=int(np.prod(shape))*[1,2,4,4][dtype];data=f.read(size)
            if len(data)!=size or name in entries:raise ValueError('raw truncation or duplicate')
            entries[name]=(dtype,shape,data)
        if f.read(1):raise ValueError('trailing bytes')
    return entries

def tensor(entry):
    import torch
    dtype,shape,data=entry
    value=torch.frombuffer(bytearray(data),dtype=[torch.int8,torch.bfloat16,torch.float32,torch.int32][dtype]).clone()
    return value.reshape(shape)

def load(root,raw,workspace,device):
    import torch
    from torch import nn
    from dataclasses import replace
    entries=read_raw(raw)
    manifest=materialize(root/'external/fx2-cmix-transformer-v1',workspace)
    package=load_package(workspace)
    model_module=importlib.import_module(package+'.model')
    exporter=importlib.import_module(package+'.export_weights')
    cfg=replace(exporter.make_reference_config(),attention_implementation='sdpa')
    model=model_module.Transformer(cfg)
    expected=[205,192,12,64,3,768,1024,64,3,4,10000]
    if tensor(entries['config.ints']).tolist()!=expected:raise ValueError('architecture differs')
    if tensor(entries['config.kimi']).tolist()!=[1,1,1,0]*3:raise ValueError('attention schedule differs')
    if tensor(entries['config.actq_dynamic_mm']).tolist()!=[1]:raise ValueError('activation path differs')
    grid=float(tensor(entries['config.codebook_grid'])[0])

    class WeightQuant(nn.Module):
        def __init__(self,prefix):
            super().__init__()
            self.scale=nn.Parameter(tensor(entries[prefix+'.weight.scale']).float())
            self.register_buffer('initial_indices',tensor(entries[prefix+'.weight.q']).long())
            self.register_buffer('levels',tensor(entries[prefix+'.weight.codebook']).float()*grid
                if prefix+'.weight.codebook' in entries else torch.arange(-127,128,dtype=torch.float32))
            self.small=prefix+'.weight.codebook' not in entries
            self.quant=replace(exporter.make_reference_config().mlp_quantization.weight,buckets=255 if self.small else 15)
        def indices(self,x):
            scale=self.scale.to(torch.bfloat16).float().reshape(-1,1)
            if (scale==0).any():raise ValueError('zero released scale')
            z=x.float()/scale
            if self.small:return z.round().clamp(-127,127).long()
            # Monotone codebook; nearest distance with original-index tie retention.
            distances=(z.unsqueeze(-1)-self.levels).abs()
            nearest=distances.argmin(-1)
            initial=self.initial_indices+7
            initial_distance=distances.gather(-1,initial.unsqueeze(-1)).squeeze(-1)
            nearest=torch.where(initial_distance==distances.min(-1).values,initial,nearest)
            return nearest-7
        def forward(self,x,initialize_scales_steps=None,return_ints=False):
            if initialize_scales_steps is not None:raise ValueError('released scales must not be initialized')
            q=self.indices(x)
            if return_ints:return q
            stored=self.scale.to(torch.bfloat16).float()
            scale=self.scale+(stored-self.scale).detach()
            values=q.float() if self.small else self.levels[q+7]
            decoded=values*scale.reshape(-1,1)
            return x+(decoded-x).detach()

    class DynamicActivation(nn.Module):
        def forward(self,x,initialize_scales_steps=None,return_ints=False):
            if initialize_scales_steps is not None:raise ValueError('no static dynamic activation scale')
            scale=x.float().abs().amax(-1,keepdim=True).clamp_min(1e-12)/127.0
            q=(x.float()/scale).round().clamp(-128,127)
            if return_ints:return q.long()
            decoded=(q*scale).type_as(x)
            return x+(decoded-x).detach()

    modules=dict(model.named_modules());consumed=set()
    for prefix,module in modules.items():
        if isinstance(module,(model_module.CastedLinear,model_module.CastedEmbedding)) and prefix+'.weight.q' in entries:
            quant=WeightQuant(prefix);module.quantize_weight=quant
            decoded=quant.initial_indices.float() if quant.small else quant.levels[quant.initial_indices+7]
            module.weight=nn.Parameter(decoded*quant.scale.detach().reshape(-1,1))
            consumed.update([prefix+'.weight.q',prefix+'.weight.scale'])
            if prefix+'.weight.codebook' in entries:consumed.add(prefix+'.weight.codebook')
        if isinstance(module,model_module.CastedLinear) and module.quantize_activation is not None:
            module.quantize_activation=DynamicActivation()
    for name,param in model.named_parameters():
        if name.endswith('.quantize_weight.scale') or name.removesuffix('.weight')+'.weight.q' in entries:
            continue
        if name not in entries:raise ValueError('missing released parameter: '+name)
        value=tensor(entries[name]).float()
        if value.numel()!=param.numel():raise ValueError('shape differs: '+name)
        with torch.no_grad():param.copy_(value.reshape(param.shape))
        consumed.add(name)
    missing=[n for n in entries if n not in consumed and not n.startswith(('config.','rope.'))]
    if missing:raise ValueError('unconsumed released tensors: '+str(missing))
    # Use released CUDA-generated RoPE bits rather than recomputing on AMD.
    sin=tensor(entries['rope.sin']);cos=tensor(entries['rope.cos'])
    model_module.make_rope_args=lambda sequence_length,cfg,device:model_module.RoPEArgs(
        sines=sin[:sequence_length].to(device),cosines=cos[:sequence_length].to(device))
    model=model.to(device)
    export_control=[]
    for prefix,module in model.named_modules():
        if isinstance(getattr(module,'quantize_weight',None),WeightQuant):
            q=module.quantize_weight.indices(module.weight)
            equal=torch.equal(q,module.quantize_weight.initial_indices)
            export_control.append({'prefix':prefix,'indices_equal':equal})
            if not equal:raise ValueError('unchanged export changed indices: '+prefix)
    return model,manifest,export_control
