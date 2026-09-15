import ctypes
import random
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path

from lib.fx2_wrt_elision_v1 import Grammar, code, swap
from tools.fx2_wrt_native_adapter_v1 import ROOT, ZIP, HEADER, mutate, CHANGED
from tools.causal_field_parent_coder_v1 import Encoder


class NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix='wrt-native-')
        cls.p = Path(cls.tmp.name)
        cls.header = (ROOT/HEADER).read_bytes()
        (cls.p/'gamma-wrt.h').write_bytes(cls.header)
        (cls.p/'bridge.cpp').write_text('''#include "gamma-wrt.h"
extern "C" void init(unsigned n,const unsigned char*v){std::vector<bool>x(256);for(int i=0;i<256;++i)x[i]=v[i];gamma_wrt::grammar.init(n,x);}
extern "C" void feed(const unsigned char*b,unsigned n,unsigned char*out){auto&g=gamma_wrt::grammar;for(unsigned i=0;i<n;++i)for(int j=7;j>=0;--j){*out++=g.forced()+1;g.observe(b[i]>>j&1);g.state(out);out+=16;}}
extern "C" unsigned dict(const char*p){FILE*f=fopen(p,"rb");fseek(f,2,SEEK_SET);gamma_wrt::init(f,std::vector<bool>(256,true));if(ftell(f)!=2)abort();fclose(f);return gamma_wrt::grammar.count;}
''')
        subprocess.run(['/usr/bin/g++','-std=c++17','-O2','-shared','-fPIC',str(cls.p/'bridge.cpp'),'-o',str(cls.p/'bridge.so')],check=True)
        cls.dll=ctypes.CDLL(str(cls.p/'bridge.so'))
        cls.dll.init.argtypes=[ctypes.c_uint,ctypes.c_char_p]
        cls.dll.feed.argtypes=[ctypes.c_char_p,ctypes.c_uint,ctypes.c_void_p]
        cls.dll.dict.argtypes=[ctypes.c_char_p];cls.dll.dict.restype=ctypes.c_uint

    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()

    def compare(self,n,body,vocab):
        self.dll.init(n,bytes(int(c in vocab) for c in range(256)))
        out=ctypes.create_string_buffer(len(body)*8*17)
        self.dll.feed(body,len(body),out)
        g=Grammar(n,vocab);p=0;data=out.raw
        for c in body:
            for j in range(7,-1,-1):
                f=g.forced();self.assertEqual(data[p],0 if f is None else f+1)
                g.observe(c>>j&1);self.assertEqual(data[p+1:p+17],g.state());p+=17
        g.finish()

    def test_dictionary_boundaries_and_shared_prefixes(self):
        for n in (1,79,80,81,3919,3920,3921,44880):
            indices=sorted({0,n-1,*range(max(0,n-5),n),*(i for i in (79,80,2639,2640,3919,3920) if i<n)})
            body=b'\x07'+b''.join(bytes(map(swap,code(i))) for i in indices)
            self.compare(n,body,set(range(256)))

    def test_all_dictionary_codes(self):
        body=b'\x07'+b''.join(bytes(map(swap,code(i))) for i in range(44880))
        self.compare(44880,body,set(range(256)))

    def test_escapes_case_and_restricted_vocabulary(self):
        rng=random.Random(728);events=[b'\x07']
        for _ in range(500):
            k=rng.randrange(3)
            if k==0: events.append(bytes([12,rng.choice([6,7,12,64,*range(128,256)])]))
            elif k==1: events.append(bytes([rng.choice([6,7,64])])+code(rng.randrange(44880)))
            else: events.append(bytes([rng.choice([10,32,97,98])]))
        body=bytes(map(swap,b''.join(events)));self.compare(44880,body,set(body))

    def test_dictionary_parser_restores_offset(self):
        p=self.p/'words';p.write_bytes(b'the\r\nword!last')
        self.assertEqual(self.dll.dict(str(p).encode()),2)

    def test_adapter_scope_and_native_coder_update_schedule(self):
        parent,child=mutate((ROOT/ZIP).read_bytes(),self.header)
        self.assertEqual({n for n in parent if parent[n]!=child[n]},set(CHANGED))
        with self.assertRaises(ValueError):mutate(b'bad',self.header)
        q=self.p/'codec';(q/'src/coder').mkdir(parents=True)
        (q/'src/gamma-wrt.h').write_bytes(self.header)
        (q/'src/predictor.h').write_text('''#pragma once
class Predictor { public: unsigned s=1,calls=0,updates=0; float Predict(){++calls;return (s&1023)/1024.0f;} void Perceive(int b){++updates;s=s*1664525u+1013904223u+b;} };
''')
        for k in ('encoder','decoder'):
            for ext in ('cpp','h'):
                name='src/coder/'+k+'.'+ext;(q/name).write_bytes(child[name] if ext=='cpp' else parent[name])
        (q/'main.cpp').write_text('''#include "src/coder/encoder.h"
#include "src/coder/decoder.h"
#include "src/gamma-wrt.h"
#include <fstream>
#include <iterator>
#include <iostream>
int main(int argc,char**v){std::ifstream f(v[1],std::ios::binary);std::vector<unsigned char>b((std::istreambuf_iterator<char>(f)),{});Predictor p;gamma_wrt::grammar.init(44880,std::vector<bool>(256,true));{std::ofstream o(v[2],std::ios::binary);Encoder e(&o,&p);for(auto c:b)for(int j=7;j>=0;--j)e.Encode(c>>j&1);e.Flush();}gamma_wrt::grammar.finish();Predictor d;gamma_wrt::grammar.init(44880,std::vector<bool>(256,true));{std::ifstream i(v[2],std::ios::binary);Decoder x(&i,&d);for(auto c:b)for(int j=7;j>=0;--j)if(x.Decode()!=(c>>j&1))return 3;}gamma_wrt::grammar.finish();if(p.calls!=b.size()*8||p.updates!=p.calls||d.calls!=p.calls||d.updates!=p.updates||d.s!=p.s)return 4;std::cout<<p.s;}
''')
        body=b'\x07'+bytes(map(swap,b'\x40'+code(40000)+b' \x0c\xffabc '+code(3000)))
        (q/'body').write_bytes(body)
        for arm in ('K','D'):
            cmd=['/usr/bin/g++','-std=c++17','-O2']
            if arm=='K':cmd+=['-DGAMMA_WRT_BOOKKEEPING']
            subprocess.run(cmd+['main.cpp','src/coder/encoder.cpp','src/coder/decoder.cpp','-o',arm],cwd=q,check=True)
            subprocess.run([str(q/arm),str(q/'body'),str(q/(arm+'.arc'))],check=True,stdout=subprocess.DEVNULL)
            g=Grammar(44880,set(range(256)));e=Encoder(max_bits=8*len(body),max_payload_bytes=1000);s=1
            for c in body:
                for j in range(7,-1,-1):
                    y=c>>j&1;p=1+int(65534*((s&1023)/1024))
                    if arm=='K' or g.forced() is None:e.encode(y,p)
                    g.observe(y);s=(s*1664525+1013904223+y)&0xffffffff
            self.assertEqual((q/(arm+'.arc')).read_bytes(),e.finish())


if __name__=='__main__':unittest.main()
