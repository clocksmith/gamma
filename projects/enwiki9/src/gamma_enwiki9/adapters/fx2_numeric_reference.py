"""Fixed-checkpoint CPU replay and diagnostic-only native-value interventions."""
from __future__ import annotations
import importlib
import math
import struct
from pathlib import Path


def read_trace(path: Path):
    import numpy as np
    rows={};order=[]
    with path.open('rb') as f:
        while header:=f.read(12):
            if len(header)!=12: raise ValueError('truncated trace header')
            row,nkey,n=struct.unpack('<III',header)
            if row>=64 or nkey>256 or n>768: raise ValueError('trace geometry differs')
            key=f.read(nkey).decode();data=f.read(4*n)
            if len(data)!=4*n or (row,key) in rows: raise ValueError('truncated/duplicate trace')
            rows[row,key]=np.frombuffer(data,dtype='<f4').copy();order.append((row,key))
    return rows,order


def read_weights(path: Path):
    import numpy as np
    kinds={0:'i1',1:'<u2',2:'<f4',3:'<i4'};result={}
    with path.open('rb') as f:
        while header:=f.read(16):
            nkey,kind,ndim,nbytes=struct.unpack('<IIII',header)
            if nkey>256 or ndim>8 or nbytes>40000000: raise ValueError('weight dump bounds')
            shape=struct.unpack('<'+'I'*ndim,f.read(4*ndim));key=f.read(nkey).decode();data=f.read(nbytes)
            if len(data)!=nbytes or key in result: raise ValueError('weight dump truncated/duplicate')
            result[key]=(kind,np.frombuffer(data,dtype=kinds[kind]).copy().reshape(shape))
    return result


def loss_bits(probabilities,tokens,markers):
    import numpy as np
    indices=np.flatnonzero(markers[:-1]!=2)
    truth=probabilities[indices,tokens[indices+1]]
    if not np.isfinite(truth).all() or (truth<=0).any() or (truth>1).any():
        raise ValueError('invalid truth probability')
    return {'bits':math.fsum(-math.log2(float(p)) for p in truth),'predictions':len(indices)},truth


class Reference:
    def __init__(self,package,model,template,trace_limit=64):
        import torch
        self.torch=torch;self.model=model;self.template=template;self.limit=trace_limit
        self.captured={};self.inject=[];self.start=0;self.rms_calls=0
        module=importlib.import_module(package+'.model');original_rms=module.rms_norm
        def rms(x):
            value=original_rms(x)
            if self.rms_calls==0:
                value=self.force('embedding.normalized',value)
                self.save('embedding.normalized',value)
            self.rms_calls+=1
            return value
        module.rms_norm=rms
        for name,item in model.named_modules():
            if item.__class__.__name__=='Quantize' and item.batched:
                item.register_forward_hook(self.quant_hook(name))
            if item.__class__.__name__=='CastedLinear':
                item.register_forward_hook(self.linear_hook(name))
            if name.startswith('blocks.') and name.count('.')==1:
                item.register_forward_pre_hook(self.block_pre(name),with_kwargs=True)
                item.register_forward_hook(self.block_post(name))

    def save(self,key,value):
        import numpy as np
        array=value.detach().float().cpu().numpy().reshape(value.shape[1],-1)
        for i in range(min(len(array),max(0,self.limit-self.start))):
            self.captured[self.start+i,key]=array[i].copy()

    def force(self,key,value):
        edits=[r for r in self.inject if r['key']==key and self.start<=r['row']<self.start+value.shape[1]]
        if not edits:return value
        result=value.clone();flat=result.reshape(result.shape[1],-1)
        for edit in edits:
            if 'values' in edit:
                flat[edit['row']-self.start]=self.torch.tensor(edit['values'],dtype=value.dtype)
            else:
                flat[edit['row']-self.start,edit['coordinate']]=edit['native']
        return result

    def quant_hook(self,name):
        def hook(module,args,out):
            torch=self.torch
            original=module.reshape_input(args[0])
            scale=module.scale.detach().to(torch.bfloat16).float().view(1,-1,1).expand_as(original)
            integer=(module.reshape_input(out)/scale).round()
            shaped=integer.reshape_as(out)
            forced=self.force(name+'.integer',shaped)
            result=(forced.reshape_as(integer)*scale).reshape_as(out)
            # Multiplication by a represented BF16 scale is exact for these bounded integers.
            self.save(name+'.input',args[0]);self.save(name+'.scale',scale.reshape_as(out))
            self.save(name+'.scaled',(original/scale).reshape_as(out));self.save(name+'.integer',forced)
            return result
        return hook

    def linear_hook(self,name):
        def hook(module,args,out):
            import numpy as np
            torch=self.torch
            value=self.force(name+'.output',out)
            self.save(name+'.output',value)
            if module.quantize_weight is not None:
                weight=self.template[name+'.weight.q'][1].astype(np.int32)
                for row in range(self.start,min(self.start+out.shape[1],self.limit)):
                    q=self.captured[row,name+'.quantize_activation.integer'].astype(np.int32)
                    # Reconstructed integer dot, not a claim that Torch used integer accumulation.
                    self.captured[row,name+'.accumulator']=(weight@q).astype(np.float32)
            return value
        return hook

    def block_pre(self,name):
        def hook(module,args,kwargs):self.save(name+'.input',args[0])
        return hook

    def block_post(self,name):
        def hook(module,args,out):self.save(name+'.output',out)
        return hook

    def replay(self,tokens,markers,priors,inject=()):
        import numpy as np
        torch=self.torch;self.captured={};self.inject=list(inject)
        logits=np.zeros((len(tokens),205),dtype='<f4');prob=np.zeros_like(logits)
        self.model.eval()
        with torch.no_grad():
            start=0
            while start<len(tokens):
                if markers[start]==2:start+=1;continue
                if markers[start]!=1:raise ValueError('reference needs an actual native reset')
                end=start+1
                while end<len(tokens) and markers[end]!=2:
                    if markers[end]==1:raise ValueError('unexplained reset')
                    end+=1
                self.start=start;self.rms_calls=0
                value=self.model.compute_logits(torch.from_numpy(tokens[start:end].astype(np.int64)).reshape(1,-1),
                    torch.from_numpy(priors[start:end].astype(np.float32)).unsqueeze(0),
                    torch.tensor([[0,end-start]],dtype=torch.int32))[0]
                logits[start:end]=value.numpy();prob[start:end]=value.softmax(-1).numpy()
                start=end+1
        return logits,prob,dict(self.captured)


def first_difference(native,reference,order,*,suffix=None):
    import numpy as np
    for row,key in order:
        if suffix is not None and not key.endswith(suffix):continue
        if (row,key) not in reference:raise ValueError('missing reference observation '+key)
        a,b=native[row,key],reference[row,key]
        if a.shape!=b.shape:raise ValueError('trace shape mismatch: '+key)
        # Integers have one zero. Their float transport must not turn -0.0 into
        # a different quantizer bin; floating observations remain bit-exact.
        different=np.flatnonzero(a!=b if key.endswith('.integer') else a.view(np.uint32)!=b.view(np.uint32))
        if len(different):
            i=int(different[0]);result={'row':row,'key':key,'coordinate':i,'native':float(a[i]),'reference':float(b[i])}
            prefix=key.removesuffix('.integer')
            for part in ['input','scaled','scale']:
                probe=prefix+'.'+part
                if (row,probe) in native:
                    result[part]={'native':float(native[row,probe][i]),'reference':float(reference[row,probe][i])}
            return result
    return None


def differences(native,reference,order):
    import numpy as np
    counts={'floating_elements_different':0,'integer_elements_different':0,'compared_elements':0}
    for pair in order:
        a,b=native[pair],reference[pair]
        n=int((a!=b if pair[1].endswith('.integer') else a.view(np.uint32)!=b.view(np.uint32)).sum());counts['compared_elements']+=a.size
        counts['integer_elements_different' if pair[1].endswith('.integer') else 'floating_elements_different']+=n
    return counts
