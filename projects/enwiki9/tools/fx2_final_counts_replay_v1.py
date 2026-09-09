#!/usr/bin/env python3
"""Exact conditional replay of final-parent residual counts; no native inference."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import struct

from causal_field_parent_coder_v1 import Encoder, Decoder
from wrt_exact import parse_store_bytes, read_dictionary_words

PREFIX=46
STATE=4612
MAX_RAW=250000
MAX_MODELED=1000000


def require(ok,message):
    if not ok:raise ValueError(message)


def digest(data):return hashlib.sha256(data).hexdigest()


class Model:
    def __init__(self,library,arm):
        self.lib=ctypes.CDLL(str(library))
        signatures={'model_new':([ctypes.c_char],ctypes.c_void_p),
                    'model_delete':([ctypes.c_void_p],None),
                    'model_predict':([ctypes.c_void_p,ctypes.c_uint],ctypes.c_int),
                    'model_observe':([ctypes.c_void_p,ctypes.c_uint],ctypes.c_int),
                    'model_state':([ctypes.c_void_p,ctypes.c_void_p],ctypes.c_uint)}
        for name,(args,result) in signatures.items():
            f=getattr(self.lib,name);f.argtypes=args;f.restype=result
        self.handle=self.lib.model_new(arm.encode())
        require(self.handle,'native initialization failed')
        self.buffer=ctypes.create_string_buffer(STATE)

    def predict(self,p):
        q=self.lib.model_predict(self.handle,p)
        require(1<=q<65536,'native prediction failed');return q

    def observe(self,y):require(self.lib.model_observe(self.handle,y)==1,'native update failed')

    def state(self):
        require(self.lib.model_state(self.handle,self.buffer)==STATE,'native state size differs')
        # Arm is a fixed invocation parameter, recorded separately. K/D common
        # learned states must match; only this one arm byte is normalized.
        return self.buffer.raw[:4]+b'D'+self.buffer.raw[5:]

    def close(self):
        if self.handle:self.lib.model_delete(self.handle);self.handle=None


def framing(prefix,modeled_count):
    require(len(prefix)==PREFIX and prefix[:5]==b'GFV1\x07','unsupported native framing')
    raw_bytes=int.from_bytes(prefix[5:9],'big')
    require(0<=raw_bytes<=MAX_RAW and 1<=modeled_count<=MAX_MODELED,'population bound differs')
    require(int.from_bytes(prefix[9:14],'big')==(1<<39)+modeled_count,'modeled framing differs')
    allowed={v for v in range(256) if prefix[14+v//8]&(1<<(v%8))}
    require(bool(allowed),'empty vocabulary');return raw_bytes,allowed


def project(trace,modeled,archive):
    require(len(trace)==28*8*len(modeled),'trace length differs')
    _,allowed=framing(archive[:PREFIX],len(modeled))
    require(all(v in allowed for v in modeled),'modeled vocabulary differs')
    encoder=Encoder(max_bits=8*len(modeled),max_payload_bytes=2*MAX_MODELED)
    q16=bytearray()
    for i,row in enumerate(struct.iter_unpack('<7I',trace)):
        _,p,lo,hi,after_lo,after_hi,y=row
        require(y==((modeled[i//8]>>(7-i%8))&1),'trace truth differs at bit '+str(i))
        require((lo,hi)==(encoder.low,encoder.high),'parent pre-interval differs at bit '+str(i))
        encoder.encode(y,p)
        require((after_lo,after_hi)==(encoder.low,encoder.high),'parent post-interval differs at bit '+str(i))
        q16.extend(struct.pack('<H',p))
    require(archive==archive[:PREFIX]+encoder.finish(),'parent exact archive replay differs')
    return bytes(q16)


def replay(operation,body,q16,prefix,words,arm,library,raw_sha256):
    require(operation in ('encode','decode','repeat') and arm in ('P','K','D','S'),'operation or arm differs')
    require(len(q16)%16==0 and 16<=len(q16)<=16*MAX_MODELED,'Q16 length differs')
    events=len(q16)//2;count=events//8;raw_bytes,allowed=framing(prefix,count)
    if operation=='decode':
        require(body[:PREFIX]==prefix and PREFIX<len(body)<=PREFIX+2*MAX_MODELED,'archive length or prefix differs')
        payload=body[PREFIX:]
        decoder=Decoder(payload,max_bits=events,max_payload_bytes=2*MAX_MODELED,
                        expected_payload_bytes=len(payload),payload_sha256=digest(payload))
    else:
        require(len(body)==count and all(v in allowed for v in body),'modeled length or vocabulary differs')
        decoder=None
    encoder=Encoder(max_bits=events,max_payload_bytes=2*MAX_MODELED)
    model=Model(library,arm);modeled=bytearray(count)
    state_hash=hashlib.sha256(b'final-counts-complete-model-v1\0')
    trajectory=hashlib.sha256(b'final-counts-common-interval-v1\0')
    probabilities=hashlib.sha256();checkpoints=[];changed=0
    try:
        for i,(p,) in enumerate(struct.iter_unpack('<H',q16)):
            q=model.predict(p);changed+=q!=p
            probabilities.update(struct.pack('<H',q));state_hash.update(b'P'+model.state())
            y=decoder.decode(q) if decoder else ((body[i//8]>>(7-i%8))&1)
            encoder.encode(y,q)
            if decoder:require((decoder.low,decoder.high)==(encoder.low,encoder.high),'decoder interval divergence at bit '+str(i))
            modeled[i//8]=(modeled[i//8]<<1)|y
            model.observe(y);state_hash.update(b'O'+model.state())
            trajectory.update(struct.pack('<HII',q,encoder.low,encoder.high))
            if (i+1)%2048==0 or i+1==events:
                checkpoints.append([i+1,state_hash.hexdigest(),trajectory.hexdigest()])
        final_state=digest(model.state())
    finally:model.close()
    require(all(v in allowed for v in modeled),'decoded vocabulary differs')
    # WRT state cannot affect predictions in this candidate; expand only after
    # decoding the complete bounded modeled stream. The inverse is unchanged.
    raw=parse_store_bytes(b'\x07'+raw_bytes.to_bytes(4,'big')+modeled,words).decoded
    require(len(raw)==raw_bytes,'raw reconstruction length differs')
    require(digest(raw)==raw_sha256,'raw reconstruction digest differs')
    archive=prefix+encoder.finish()
    if decoder:require(archive==body,'noncanonical or truncated arithmetic payload')
    result=dict(arm=arm,raw_bytes=len(raw),raw_sha256=digest(raw),modeled_bytes=count,
                modeled_sha256=digest(modeled),events=events,changed_q16_events=changed,
                archive_bytes=len(archive),archive_sha256=digest(archive),
                model_state_boundaries=2*events,model_state_sha256=state_hash.hexdigest(),
                final_model_state_sha256=final_state,probability_sha256=probabilities.hexdigest(),
                common_coder_trajectory_sha256=trajectory.hexdigest(),checkpoints=checkpoints,
                parent_q16_bytes=len(q16),parent_q16_sha256=digest(q16),
                exact_inverse=True,standalone_decoder=False,objective_credit_bytes=0,
                complete_package_bytes=None,full_corpus_score_bytes=None)
    return archive,raw,bytes(modeled),result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=('project','encode','decode','repeat'))
    for name in ('input','output','report'):parser.add_argument('--'+name,required=True,type=Path)
    for name in ('trace','parent','q16','dictionary','library'):parser.add_argument('--'+name,type=Path)
    parser.add_argument('--prefix');parser.add_argument('--arm',choices=tuple('PKDS'))
    parser.add_argument('--raw-sha256')
    parser.add_argument('--modeled-output',type=Path)
    args=parser.parse_args()
    def write(path,data):
        with path.open('xb') as stream:stream.write(data)
    if args.operation=='project':
        require(args.input.stat().st_size<=MAX_MODELED and args.trace.stat().st_size<=MAX_MODELED*8*28,'projection input bound')
        q16=project(args.trace.read_bytes(),args.input.read_bytes(),args.parent.read_bytes())
        write(args.output,q16);result=dict(parent_q16_bytes=len(q16),parent_q16_sha256=digest(q16),native_parent_payload_exact=True)
    else:
        for path,cap in [(args.input,PREFIX+2*MAX_MODELED),(args.q16,16*MAX_MODELED),(args.dictionary,16*1024**2)]:
            require(path.stat().st_size<=cap,'input file bound differs')
        archive,raw,modeled,result=replay(args.operation,args.input.read_bytes(),args.q16.read_bytes(),
            bytes.fromhex(args.prefix),read_dictionary_words(args.dictionary),args.arm,args.library,args.raw_sha256)
        write(args.output,raw if args.operation=='decode' else archive)
        if args.modeled_output:write(args.modeled_output,modeled)
    write(args.report,(json.dumps(result,sort_keys=True,indent=2)+'\n').encode())
    print(json.dumps({k:v for k,v in result.items() if k!='checkpoints'},sort_keys=True))


if __name__=='__main__':main()
