"""Bind a depth-one persistent relational transducer to the unchanged FX2 coder."""
from __future__ import annotations
import hashlib
from pathlib import Path
from .fx2_training_capture import source_members
from .fx2_title_native import METHODS


def runtime_header():
    # Reuse the identity-checked dictionary reader; no neural metadata adapter.
    start=METHODS.index('  struct stat info;')
    end=METHODS.index('  title_memory_.reset')
    reader=METHODS[start:end].replace('Fail(', 'die(')
    return r'''#pragma once
#include "predictors/causal_relational_v1.hpp"
#include <memory>
#include <sys/stat.h>
#include <unistd.h>
#include <cerrno>
#include <cstdio>
#include <cstring>
#include <cmath>
namespace gamma_relation_runtime {
inline void die(const char* text){std::fprintf(stderr,"%s\n",text);std::abort();}
inline std::unique_ptr<gamma_relational::Model> model;
inline FILE *raw_file=nullptr,*state_file=nullptr,*parent_file=nullptr;
inline std::string prefix;
inline long double parent_bits=0,relation_bits=0,mixed_bits=0,active_parent_bits=0,active_mixed_bits=0;
inline void write(FILE* f,const gamma_xml_field::Bytes& b){if(f&&std::fwrite(b.data(),1,b.size(),f)!=b.size())die("relational witness write");}
inline void witness(){auto s=model->state();gamma_xml_field::Bytes h;gamma_relational::put(h,model->modeled());gamma_relational::put(h,s.size());write(state_file,h);write(state_file,s);}
inline void begin(FILE* dictionary,const char* header,uint64_t expected_raw){
 if(!dictionary||!header||header[0]!=7||model)die("relational requires one native dictionary TEXT block");
''' + reader + r'''
 const char* selected=std::getenv("GAMMA_RELATIONAL_ARM");
 if(!selected||std::strlen(selected)!=1)die("relational arm required");
 model.reset(new gamma_relational::Model(words,raw_length,selected[0]));
 const char* output=std::getenv("GAMMA_RELATIONAL_CAPTURE");
 if(output){prefix=output;raw_file=std::fopen((prefix+".raw").c_str(),"wbx");state_file=std::fopen((prefix+".state").c_str(),"wbx");parent_file=std::fopen((prefix+".parent").c_str(),"wbx");if(!raw_file||!state_file||!parent_file)die("relational capture create");}
}
inline uint32_t predict(uint32_t p){if(!model)die("relational missing initialization");return model->predict(p);}
inline void observe(unsigned bit){
 const auto before=model->active_bits;
 const auto p=model->parent(),q=model->relational(),m=model->mixed();
 auto loss=[bit](uint32_t v){return -std::log2((long double)(bit?v:65536-v)/65536);};
 parent_bits+=loss(p);relation_bits+=loss(q);mixed_bits+=loss(m);
 // q!=p is a prediction-time measurable opportunity, not a truth-selected subset.
 if(q!=p){active_parent_bits+=loss(p);active_mixed_bits+=loss(m);}
 if(parent_file){const unsigned char row[3]={uint8_t(p),uint8_t(p>>8),uint8_t(bit)};if(std::fwrite(row,1,3,parent_file)!=3)die("parent trace write");}
 gamma_xml_field::Bytes raw;if(!model->observe(bit,raw))die("relational inverse failed");write(raw_file,raw);
 (void)before;
 if(model->modeled()&&model->modeled()%gamma_relational::Epoch==0&&raw.size())witness();
}
inline void end(){
 if(!model||!model->finish())die("relational inverse terminal failed");
 witness();
 for(FILE* f:{raw_file,state_file,parent_file})if(f&&std::fclose(f))die("relational capture close");
 if(!prefix.empty()){
 FILE* f=std::fopen((prefix+".json").c_str(),"wx");if(!f)die("relational summary create");
 std::fprintf(f,"{\"modeled_bytes\":%llu,\"active_bits\":%llu,\"mentions\":%llu,\"donor_pairs\":%llu,\"parent_bits\":%.18Lg,\"relation_bits\":%.18Lg,\"mixed_bits\":%.18Lg,\"active_parent_bits\":%.18Lg,\"active_mixed_bits\":%.18Lg}\n",(unsigned long long)model->modeled(),(unsigned long long)model->active_bits,(unsigned long long)model->mentions,(unsigned long long)model->pairs,parent_bits,relation_bits,mixed_bits,active_parent_bits,active_mixed_bits);
 if(std::fclose(f))die("relational summary close");}
 model.reset();
}
}
'''


def adapt(source_zip: Path, library: Path):
    members=source_members(source_zip); receipts=[]
    changes={'src/runner.cpp':[
        ('#include "predictor.h"','#include "predictor.h"\n#include "gamma-relational-runtime.h"'),
        ('  Compress(temp_bytes, &temp_in, &data_out, output_bytes, &p);', '  gamma_relation_runtime::begin(dictionary, gamma_static_frontend ? gamma_literal_header : nullptr, *input_bytes);\n  Compress(temp_bytes, &temp_in, &data_out, output_bytes, &p);\n  gamma_relation_runtime::end();'),
        ('  Decompress(*output_bytes, &data_in, &temp_out, &p);', '  gamma_relation_runtime::begin(dictionary, gamma_static_frontend ? gamma_literal_header : nullptr, 0);\n  Decompress(*output_bytes, &data_in, &temp_out, &p);\n  gamma_relation_runtime::end();')]}
    for n in ('encoder','decoder'):
        changes['src/coder/'+n+'.cpp']=[
            ('#include "'+n+'.h"','#include "'+n+'.h"\n#include "../gamma-relational-runtime.h"'),
            ('  const unsigned int xmid =', '  p = gamma_relation_runtime::predict(p);\n  const unsigned int xmid ='),
            ('  p_->Perceive(bit);','  gamma_relation_runtime::observe(bit);\n  p_->Perceive(bit);')]
    for name,replacements in changes.items():
        before=members[name];text=before.decode()
        for old,new in replacements:
            if text.count(old)!=1:raise ValueError('ambiguous relational anchor: '+name)
            text=text.replace(old,new)
        members[name]=text.encode();receipts.append({'path':name,'preimage_sha256':hashlib.sha256(before).hexdigest(),'postimage_sha256':hashlib.sha256(members[name]).hexdigest()})
    additions={'src/gamma-relational-runtime.h':runtime_header().encode(),**{'src/'+n:(library/n).read_bytes() for n in ['predictors/causal_relational_v1.hpp','fx2_xml_field_observer_v1.hpp']}}
    for name,raw in additions.items():
        if name in members:raise ValueError('duplicate relational source')
        members[name]=raw;receipts.append({'path':name,'postimage_sha256':hashlib.sha256(raw).hexdigest()})
    return members,receipts
