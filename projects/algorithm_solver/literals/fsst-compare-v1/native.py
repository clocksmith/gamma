"""Pinned FSST C API plus independent strict byte-level decoding and optimal paths."""
import ctypes as C
from pathlib import Path

class Decoder(C.Structure):
    _fields_=[('version',C.c_uint64),('zeroTerminated',C.c_uint8),('length',C.c_uint8*255),('symbol',C.c_uint64*255)]


def table_from_header(header):
    if len(header)<17 or header[8]!=0:raise ValueError('nonzero-terminated FSST header required')
    pos=17;table=[]
    for length in (2,3,4,5,6,7,8,1):
        for _ in range(header[9+length-1]):
            if pos+length>len(header):raise ValueError('truncated table')
            table.append(header[pos:pos+length]);pos+=length
    if pos!=len(header) or len(table)>255 or len(set(table))!=len(table):raise ValueError('invalid table')
    return table


def decode(table,payload):
    out=[];i=0
    while i<len(payload):
        code=payload[i];i+=1
        if code==255:
            if i==len(payload):raise ValueError('truncated escape')
            out.append(payload[i:i+1]);i+=1
        else:
            if code>=len(table):raise ValueError('undefined code')
            out.append(table[code])
    return b''.join(out)


def optimal(table,text):
    """Minimum native payload bytes, including two bytes per escape. Tie by payload IDs."""
    tree={}
    for i,word in enumerate(table):
        node=tree
        for ch in word:node=node.setdefault(ch,{})
        node[None]=i
    n=len(text);cost=[0]*(n+1);edges=[None]*n
    for pos in range(n-1,-1,-1):
        cost[pos]=2+cost[pos+1];edges[pos]=(bytes((255,text[pos])),pos+1)
        node=tree;end=pos
        while end<n and text[end] in node:
            node=node[text[end]];end+=1
            if None in node:
                code=node[None];value=1+cost[end]
                if (value,code)<(cost[pos],edges[pos][0][0]):cost[pos]=value;edges[pos]=(bytes((code,)),end)
    parts=[];pos=0
    while pos<n:
        piece,pos=edges[pos];parts.append(piece)
    return b''.join(parts)


def counts(table,payload):
    codes=escapes=characters=0;uses=[0]*len(table);pos=0
    while pos<len(payload):
        code=payload[pos];pos+=1;codes+=1
        if code==255:
            if pos==len(payload):raise ValueError('truncated escape')
            pos+=1;escapes+=1;characters+=2;codes+=1
        else:
            if code>=len(table):raise ValueError('undefined code')
            uses[code]+=1;characters+=int(len(table[code])==1)
    return {'selections':codes,'escapes':escapes,'single_character_channel_codes':characters,'symbol_uses':uses}


class Encoder:
    def __init__(self,library,fit):
        self.lib=C.CDLL(str(Path(library).resolve()));lib=self.lib
        P=C.c_void_p;Z=C.c_size_t;B=C.POINTER(C.c_ubyte)
        lib.fsst_create.argtypes=[Z,C.POINTER(Z),C.POINTER(P),C.c_int];lib.fsst_create.restype=P
        lib.fsst_destroy.argtypes=[P];lib.fsst_destroy.restype=None
        lib.fsst_export.argtypes=[P,B];lib.fsst_export.restype=C.c_uint
        lib.fsst_import.argtypes=[C.POINTER(Decoder),B];lib.fsst_import.restype=C.c_uint
        lib.fsst_compress.argtypes=[P,Z,C.POINTER(Z),C.POINTER(P),Z,B,C.POINTER(Z),C.POINTER(P)];lib.fsst_compress.restype=Z
        lib.gamma_fsst_decode.argtypes=[C.POINTER(Decoder),Z,P,Z,B];lib.gamma_fsst_decode.restype=Z
        lib.gamma_fsst_decoder_size.restype=Z
        assert lib.gamma_fsst_decoder_size()==C.sizeof(Decoder)
        self.handle=None
        buffers,sizes,pointers=self.batch(fit)
        if not fit or not any(fit):raise ValueError('nonempty fitting bytes required')
        self.handle=lib.fsst_create(len(fit),sizes,pointers,0)
        if not self.handle:raise RuntimeError('FSST create failed')
        header=(C.c_ubyte*2066)();length=lib.fsst_export(self.handle,header);self.header=bytes(header[:length])
        self.decoder=Decoder();assert lib.fsst_import(C.byref(self.decoder),header)==length
        self.table=table_from_header(self.header)
        for i,word in enumerate(self.table):
            assert self.decoder.length[i]==len(word) and bytes(self.decoder.symbol[i].to_bytes(8,'little'))[:len(word)]==word
    @staticmethod
    def batch(texts):
        buffers=[C.create_string_buffer(text) for text in texts]
        sizes=(C.c_size_t*len(texts))(*map(len,texts));pointers=(C.c_void_p*len(texts))(*map(C.addressof,buffers))
        return buffers,sizes,pointers
    def compress(self,texts):
        buffers,sizes,pointers=self.batch(texts);space=sum(7+2*len(s) for s in texts)+64
        output=(C.c_ubyte*space)();lengths=(C.c_size_t*len(texts))();starts=(C.c_void_p*len(texts))()
        got=self.lib.fsst_compress(self.handle,len(texts),sizes,pointers,space,output,lengths,starts)
        assert got==len(texts)
        payloads=[C.string_at(starts[i],lengths[i]) for i in range(len(texts))]
        for text,payload in zip(texts,payloads):
            assert decode(self.table,payload)==text
            self.verify_official(payload,text)
        return payloads
    def verify_official(self,payload,expected):
        source=C.create_string_buffer(payload);out=(C.c_ubyte*(len(expected)+32))()
        size=self.lib.gamma_fsst_decode(C.byref(self.decoder),len(payload),C.addressof(source),len(out),out)
        assert size==len(expected) and bytes(out[:size])==expected
    def close(self):
        if self.handle:self.lib.fsst_destroy(self.handle);self.handle=None
    def __enter__(self):return self
    def __exit__(self,*args):self.close()
