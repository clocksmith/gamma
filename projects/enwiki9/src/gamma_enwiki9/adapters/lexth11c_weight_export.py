"""Byte-exact unchanged-weight export control for the released donor import."""
from __future__ import annotations
from pathlib import Path
import struct
from .lexth11c_gpu_reference import read_raw

def unchanged_control(model, original, output):
    import torch
    entries=read_raw(original);parameters=dict(model.named_parameters());modules=dict(model.named_modules())
    checked=[]
    with Path(output).open('xb') as f:
        f.write(b'FX2TFW01');f.write(struct.pack('<I',len(entries)))
        for name,(dtype,shape,source) in entries.items():
            value=None
            if name.endswith('.weight.q'):
                m=modules[name.removesuffix('.weight.q')]
                value=m.quantize_weight.indices(m.weight).to(torch.int8)
            elif name.endswith('.weight.scale'):
                value=modules[name.removesuffix('.weight.scale')].quantize_weight.scale
            elif name.endswith('.weight.codebook'):
                value=(modules[name.removesuffix('.weight.codebook')].quantize_weight.levels/0.25).to(torch.int8)
            elif name in parameters:value=parameters[name]
            if value is None:data=source
            else:
                value=value.detach().reshape(shape)
                if dtype==1:value=value.to(torch.bfloat16).view(torch.uint16)
                else:value=value.to([torch.int8,torch.bfloat16,torch.float32,torch.int32][dtype])
                data=value.cpu().contiguous().numpy().tobytes()
            if data!=source:raise ValueError('unchanged export differs: '+name)
            encoded=name.encode();f.write(struct.pack('<I',len(encoded)));f.write(encoded)
            f.write(bytes([dtype]));f.write(struct.pack('<I',len(shape)))
            f.write(struct.pack('<'+'I'*len(shape),*shape));f.write(data)
            checked.append(name)
    return {'typed_tensor_count':len(checked),'all_dtype_shape_data_bits_equal':True,
            'before_optimizer_updates':True,'output':str(output)}
