"""Read-only numerical instrumentation of exact native source in a new workspace."""
from __future__ import annotations
import hashlib
from .fx2_training_capture import source_members


def instrument(source_zip):
    members=source_members(source_zip)
    name='cpp_infer/src/opt/model_opt.cpp'; before=members[name]; text=before.decode()
    def change(anchor, extra, *, replace=False):
        nonlocal text
        if text.count(anchor)!=1: raise ValueError('ambiguous numeric anchor: '+anchor)
        text=text.replace(anchor,extra if replace else anchor+'\n'+extra)
    change('#include "model_opt.h"','#include "fx2_numeric_trace.hpp"')
    change('const float* tok = M.tok_table + size_t(token) * D;', 'gamma_numeric::emit("embedding.normalized",tok,D);')
    change('      embed_combine192(tok, yb, x);  // x0 = tok_row + rms_norm(prior_y)',
           '      gamma_numeric::sparse("prior_embedding",M.prior,prior_f32,M.prior_s_act,q8p,V);')
    change('        axpby_tok192(M.rsc[l], x, M.tec[l], tok);',
           'gamma_numeric::layer=l; gamma_numeric::emit(gamma_numeric::block("input"),x,D);\n        axpby_tok192(M.rsc[l], x, M.tec[l], tok);',replace=True)
    change('      mlp_block(l);','gamma_numeric::emit(gamma_numeric::block("output"),x,D);')
    # Quantized linear sites; recomputed dots/rescaling observe the same immutable arenas.
    for kind,count in [('kimi',5),('van',3)]:
        anchor=('      rms_norm_quant192_multi(x, xn, s5, 5, q5);' if kind=='kimi' else
                '      rms_norm_quant192_x3(x, xn, s3, q5, q5 + D, q5 + 2 * D);')
        calls=[]
        for i,(field,site) in enumerate([('query_projection','qp'),('key_projection','kp'),('value_projection','vp')]):
            calls.append(f'gamma_numeric::dense(gamma_numeric::block("attention.{field}"),L.{site}.m,xn,L.{site}.s_act,q5+{i}*D);')
        change(anchor,'\n'.join(calls))
    for short,long,offset in [('fg','forget_gate',3),('og','output_gate',4)]:
        anchor=f'      qgemv_quant_bias(L.{short}_up.m, q5 + {offset} * D, L.{short}_down.s_act, q64b);'
        change(anchor,f'''if(gamma_numeric::active()) {{
          gamma_numeric::dense(gamma_numeric::block("attention.{long}_projection.up"),L.{short}_up.m,xn,L.{short}_up.s_act,q5+{offset}*D);
          alignas(64) float temp[64]; qgemv_f32(L.{short}_up.m,q5+{offset}*D,temp);
          gamma_numeric::dense(gamma_numeric::block("attention.{long}_projection.down"),L.{short}_down.m,temp,L.{short}_down.s_act,q64b);
        }}''')
    change('      quant192_u8(gn, L.op.s_act, q5);','gamma_numeric::dense(gamma_numeric::block("attention.output_projection"),L.op.m,gn,L.op.s_act,q5);')
    change('      quant192_u8(pre, L.op.s_act, q5);','gamma_numeric::dense(gamma_numeric::block("attention.output_projection"),L.op.m,pre,L.op.s_act,q5);')
    change('        quant64_i8(vf + h * DH, L.sv[h], vv + h * DH);','''if(h==NH-1) {
          gamma_numeric::quant(gamma_numeric::block("attention.quantize_queries"),qf,L.sq,DH,qq,0,true,D);
          gamma_numeric::quant(gamma_numeric::block("attention.quantize_keys"),kf,L.sk,DH,kk,0,true,D);
          gamma_numeric::quant(gamma_numeric::block("attention.quantize_values"),vf,L.sv,DH,vv,0,true,D);
        }''')
    change('      rms_norm_quant192(x, xn, mm.up.s_act, q5);','gamma_numeric::dense(gamma_numeric::block("mlp.up"),mm.up.m,xn,mm.up.s_act,q5);')
    change('      nnz = qgemv_relu2q(mm.up.m, q5, mm.down_s_act, q768, idx768);','''if(gamma_numeric::active()) {
        alignas(64) float temp[768]; qgemv_f32(mm.up.m,q5,temp);
        for(int i=0;i<768;++i) { const float v=std::max(temp[i],0.0f); temp[i]=v*v; }
        gamma_numeric::sparse(gamma_numeric::block("mlp.down"),mm.down,temp,mm.down_s_act,q768,768);
      }''')
    change('      rms_norm_quant192(x, xn, M.unembed.s_act, q5);','gamma_numeric::dense("unembedding",M.unembed.m,xn,M.unembed.s_act,q5);')
    members[name]=text.encode()
    return members,{'path':name,'preimage_sha256':hashlib.sha256(before).hexdigest(),
                    'postimage_sha256':hashlib.sha256(members[name]).hexdigest()}
