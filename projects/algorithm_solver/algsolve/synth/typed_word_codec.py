"""Charged fixed-codeword representation of primitive typed IR, not a solver.

Every grammar token, numeric bit and numeric terminator costs one width-bit word.
Recipes expand before encoding. Packets contain no source, text/name payload,
external recipe ID or uncharged operand. Original names are cosmetic; positional
input order and lexical resource identities survive canonical alpha-renaming.
"""
from __future__ import annotations

import hashlib
from collections import Counter
import json
from pathlib import Path
import struct

SCHEMA = 'algsolve.typed-word-codec.v1'
MAX_WORDS = 262144
HEADER = struct.Struct('>4sBBB I 32s32s32s')
MAGIC = b'TWIR'
PROFILES = {'base-v2': 0, 'vector-v1': 1}
PURE = ('add','append','empty_ints','eq','field','len','lt','mul','neg','not','range','sort_by','sub','tuple')
BASE_EFFECTS = ('dsu.find','dsu.new','dsu.union','heap.new','heap.pop','heap.push','map.get','map.has','map.new','map.set','queue.new','queue.pop','queue.push','queue.size')
VECTOR_EFFECTS = ('vector.append','vector.new','vector.snapshot')
BASE_TYPES = ('bool','dsu','heap_int','int','map_int_int','queue_int','unit')
STRUCTURE = ('PROGRAM','BLOCK','LET','VAR','SET','FOR','IF','REF','INT','TRUE','FALSE','POS','NEG','BIT0','BIT1','END')


class Invalid(ValueError):
    """Malformed, noncanonical, unbound, mistyped or version-mismatched packet."""


def require(ok, message):
    if not ok: raise Invalid(message)


def runtime(profile):
    require(profile in PROFILES,'Unknown profile')
    if profile == 'base-v2':
        from . import typed_program
        return typed_program
    from . import typed_vector_program
    return typed_vector_program


def vocabulary(profile):
    ir=runtime(profile)
    effects=BASE_EFFECTS + (VECTOR_EFFECTS if profile=='vector-v1' else ())
    atoms=BASE_TYPES + (('vector_int',) if profile=='vector-v1' else ())
    require(set(ir.PURE)==set(PURE) and set(ir.EFFECTS)==set(effects),'Runtime operation surface drift')
    require(ir.RESOURCES==set(atoms)-{'bool','int','unit'},'Runtime type surface drift')
    words=STRUCTURE+tuple('P:'+x for x in PURE)+tuple('E:'+x for x in effects)+tuple('T:'+x for x in atoms)+('T:list','T:tuple')
    require(len(words)<=64,'Six-bit vocabulary exhausted')
    return words


def dictionary_bytes(profile):
    return json.dumps({'schema':SCHEMA,'program_schema':runtime(profile).SCHEMA,
        'profile':profile,'words':vocabulary(profile),'numeric':'sign then canonical MSB binary words then END; zero=BIT0 END',
        'bindings':'explicit globally sequential declaration indices; lexical references',
        'recipes':'fully expanded; no recipe opcodes'},sort_keys=True,separators=(',',':')).encode()


def identities(profile):
    return (hashlib.sha256(dictionary_bytes(profile)).digest(),
            hashlib.sha256(Path(runtime(profile).__file__).read_bytes()).digest(),
            hashlib.sha256(Path(__file__).read_bytes()).digest())


def descriptor(profile='base-v2'):
    ir=runtime(profile); hashes=identities(profile)
    return {'schema':SCHEMA,'profile':profile,'program_schema':ir.SCHEMA,'entries':len(vocabulary(profile)),
        'words':list(vocabulary(profile)),'widths':[6,7,8],'header_bytes':HEADER.size,
        'max_words':MAX_WORDS,'max_integer_bits':ir.MAX_INTEGER_BITS,'max_graph_nodes':ir.MAX_GRAPH_NODES,
        'dictionary_sha256':hashes[0].hex(),'runtime_sha256':hashes[1].hex(),'decoder_sha256':hashes[2].hex(),
        'dictionary_bytes':len(dictionary_bytes(profile)),
        'decoder_source_bytes':Path(__file__).stat().st_size,
        'runtime_source_bytes':Path(ir.__file__).stat().st_size,
        'scope':'representation of supplied typed graphs only; not source qualification or unseen solving'}


def canonicalize(program, profile='base-v2', recipes=None):
    """Hygienic primitive expansion followed by globally indexed alpha-renaming."""
    ir=runtime(profile); expanded,_=ir.expanded(program,recipes or {})
    serial=[0]
    def fresh():
        n=serial[0]; serial[0]+=1
        return 'b'+str(n)
    names={p:fresh() for p in expanded['parameters']}
    def expr(e,scope):
        if 'ref' in e: return {'ref':scope[e['ref']]}
        if 'literal' in e: return dict(e)
        return {'op':e['op'],'args':[expr(x,scope) for x in e['args']]}
    def block(body,scope):
        out=[]
        for s in body:
            op=s['op']
            if op in ('let','var','set'):
                value=expr(s['value'],scope)
                if op!='set': scope[s['name']]=fresh()
                out.append({'op':op,'name':scope[s['name']],'value':value})
            elif op=='call':
                args=[expr(x,scope) for x in s['args']]; scope[s['out']]=fresh()
                out.append({'op':op,'operator':s['operator'],'args':args,'out':scope[s['out']]})
            elif op=='for':
                values=expr(s['in'],scope); child=dict(scope); child[s['item']]=fresh()
                out.append({'op':op,'item':child[s['item']],'in':values,'body':block(s['body'],child)})
            elif op=='if':
                out.append({'op':op,'condition':expr(s['condition'],scope),
                    'then':block(s['then'],dict(scope)),'else':block(s['else'],dict(scope))})
            else: raise Invalid('Expansion left an unsupported statement')
        return out
    scope=dict(names); body=block(expanded['body'],scope)
    result={'schema':ir.SCHEMA,'parameters':[names[p] for p in expanded['parameters']],
        'inputs':{names[p]:expanded['inputs'][p] for p in expanded['parameters']},
        'body':body,'return':expr(expanded['return'],scope),'output_type':expanded['output_type']}
    # JSON-normalize compound type tuples without changing runtime semantics.
    result=json.loads(json.dumps(result)); ir.validate(result)
    return result


def _encode_words(program, profile):
    ir=runtime(profile); vocab=vocabulary(profile); codes={w:i for i,w in enumerate(vocab)}; words=[]
    def emit(word):
        require(len(words)<MAX_WORDS,'Encoded word budget exceeded'); words.append(codes[word])
    def nat(value):
        require(type(value) is int and value>=0 and value.bit_length()<=ir.MAX_INTEGER_BITS,'Invalid bounded natural')
        for bit in bin(value)[2:]: emit('BIT'+bit)
        emit('END')
    def binding(name):
        require(name.startswith('b') and name[1:].isdigit(),'Noncanonical binding'); nat(int(name[1:]))
    def dtype(t):
        if type(t) is str: emit('T:'+t)
        elif t[0]=='list': emit('T:list'); dtype(t[1])
        else:
            emit('T:tuple'); nat(len(t)-1)
            for child in t[1:]: dtype(child)
    def args(values):
        nat(len(values))
        for value in values: expr(value)
    def expr(e):
        if 'ref' in e: emit('REF'); binding(e['ref'])
        elif 'literal' in e:
            value=e['literal']
            if type(value) is bool: emit('TRUE' if value else 'FALSE')
            else: emit('INT'); emit('NEG' if value<0 else 'POS'); nat(abs(value))
        else: emit('P:'+e['op']); args(e['args'])
    def block(body):
        emit('BLOCK'); nat(len(body))
        for s in body:
            op=s['op']
            if op in ('let','var','set'): emit(op.upper()); binding(s['name']); expr(s['value'])
            elif op=='call': emit('E:'+s['operator']); binding(s['out']); args(s['args'])
            elif op=='for': emit('FOR'); binding(s['item']); expr(s['in']); block(s['body'])
            elif op=='if': emit('IF'); expr(s['condition']); block(s['then']); block(s['else'])
            else: raise Invalid('No recipe or source escape opcode')
    emit('PROGRAM'); nat(len(program['parameters']))
    for p in program['parameters']: binding(p); dtype(program['inputs'][p])
    dtype(program['output_type']); block(program['body']); expr(program['return'])
    return words


def _packet(words,width,profile):
    require(type(width) is int and width in (6,7,8),'Width must be 6, 7 or 8')
    require(0<len(words)<=MAX_WORDS,'Word count outside budget')
    bits=''.join(format(w,f'0{width}b') for w in words)
    pad=(-len(bits))%8; bits+='0'*pad
    payload=int(bits,2).to_bytes(len(bits)//8,'big')
    return HEADER.pack(MAGIC,1,width,PROFILES[profile],len(words),*identities(profile))+payload


def costs(packet):
    profile,width,words=_unpack(packet)
    d=descriptor(profile); payload=len(words)*width; padding=(-payload)%8
    counts=Counter(vocabulary(profile)[w] for w in words)
    numeric=sum(counts[w] for w in ('BIT0','BIT1','END','POS','NEG'))
    return {'profile':profile,'width':width,'selections':len(words),'payload_bits':payload,
        'framing_bits':HEADER.size*8,'padding_bits':padding,'packet_bits':len(packet)*8,
        'numeric_and_control_selections':numeric,'numeric_and_control_bits':numeric*width,
        'word_counts':dict(sorted(counts.items())),
        'dictionary_storage_bits':d['dictionary_bytes']*8,'decoder_storage_bits':d['decoder_source_bytes']*8,
        'runtime_storage_bits':d['runtime_source_bytes']*8,
        'one_program_with_support_bits':len(packet)*8+8*(d['dictionary_bytes']+d['decoder_source_bytes']+d['runtime_source_bytes']),
        'dependency_scope':'Python interpreter and standard library are external environment dependencies, not included in source storage',
        'evidence_scope':'typed graph representation only; no native/source qualification or independent solving'}


def encode(program,width,profile='base-v2',recipes=None):
    canonical=canonicalize(program,profile,recipes)
    packet=_packet(_encode_words(canonical,profile),width,profile)
    return packet,costs(packet)


def _unpack(packet):
    require(type(packet) is bytes and HEADER.size<len(packet)<=HEADER.size+MAX_WORDS,'Invalid packet byte count')
    magic,version,width,profile_id,count,dh,rh,ch=HEADER.unpack(packet[:HEADER.size])
    require(magic==MAGIC and version==1 and width in (6,7,8),'Invalid framing')
    require(profile_id in PROFILES.values(),'Unknown profile')
    profile=next(p for p,i in PROFILES.items() if i==profile_id)
    require((dh,rh,ch)==identities(profile),'Dictionary/runtime/decoder identity mismatch')
    require(0<count<=MAX_WORDS,'Word budget exceeded')
    bits=count*width; n=(bits+7)//8
    require(len(packet)==HEADER.size+n,'Truncated/trailing packet bytes')
    packed_bits=''.join(format(byte,'08b') for byte in packet[HEADER.size:])
    pad=n*8-bits
    require(not pad or set(packed_bits[-pad:]) <= {'0'},'Nonzero padding')
    words=[int(packed_bits[i:i+width],2) for i in range(0,bits,width)]
    vocabulary_size=len(vocabulary(profile))
    require(all(w<vocabulary_size for w in words),'Unused opcode')
    return profile,width,words


def decode(packet):
    profile,width,words=_unpack(packet); ir=runtime(profile); vocab=vocabulary(profile)
    cursor=[0]; serial=[0]; constructed=[0]
    def tick(depth):
        require(depth<=ir.MAX_DEPTH,'Decode nesting budget exceeded')
        constructed[0]+=1; require(constructed[0]<=ir.MAX_GRAPH_NODES,'Decode graph budget exceeded')
    def take(expected=None):
        require(cursor[0]<len(words),'Truncated grammar'); value=vocab[words[cursor[0]]]; cursor[0]+=1
        require(expected is None or value==expected,'Unexpected grammar token')
        return value
    def nat(limit):
        bits=[]
        while True:
            word=take()
            if word=='END': break
            require(word in ('BIT0','BIT1') and len(bits)<ir.MAX_INTEGER_BITS,'Invalid/oversized structural numeral')
            bits.append(int(word=='BIT1'))
        require(bits and (len(bits)==1 or bits[0]==1),'Noncanonical structural numeral')
        value=0
        for bit in bits: value=(value<<1)|bit
        require(value<=limit,'Structural count/index outside budget')
        return value
    def binding(declare=False):
        number=nat(ir.MAX_GRAPH_NODES)
        if declare:
            require(number==serial[0],'Noncanonical declaration index'); serial[0]+=1
        return 'b'+str(number)
    def dtype(depth):
        tick(depth); token=take(); require(token.startswith('T:'),'Expected type')
        tag=token[2:]
        if tag=='list': return ['list',dtype(depth+1)]
        if tag=='tuple': return ['tuple']+[dtype(depth+1) for _ in range(nat(ir.MAX_GRAPH_NODES))]
        return tag
    def args(depth):
        count=nat(ir.MAX_GRAPH_NODES)
        return [expr(depth+1) for _ in range(count)]
    def expr(depth):
        tick(depth); token=take()
        if token=='REF': return {'ref':binding()}
        if token in ('TRUE','FALSE'): return {'literal':token=='TRUE'}
        if token=='INT':
            sign=take(); require(sign in ('POS','NEG'),'Expected sign')
            value=nat((1<<ir.MAX_INTEGER_BITS)-1)
            require(sign!='NEG' or value!=0,'Negative zero is noncanonical')
            return {'literal':-value if sign=='NEG' else value}
        require(token.startswith('P:'),'Expected primitive expression')
        return {'op':token[2:],'args':args(depth)}
    def block(depth):
        tick(depth); take('BLOCK'); count=nat(ir.MAX_GRAPH_NODES); body=[]
        for _ in range(count):
            tick(depth); token=take()
            if token in ('LET','VAR','SET'):
                name=binding(token!='SET'); body.append({'op':token.lower(),'name':name,'value':expr(depth+1)})
            elif token.startswith('E:'):
                name=binding(True); body.append({'op':'call','operator':token[2:],'out':name,'args':args(depth)})
            elif token=='FOR':
                item=binding(True); values=expr(depth+1)
                body.append({'op':'for','item':item,'in':values,'body':block(depth+1)})
            elif token=='IF':
                condition=expr(depth+1); yes=block(depth+1); no=block(depth+1)
                body.append({'op':'if','condition':condition,'then':yes,'else':no})
            else: raise Invalid('Expected primitive statement')
        return body
    try:
        take('PROGRAM'); count=nat(ir.MAX_GRAPH_NODES); parameters=[]; inputs={}
        for _ in range(count):
            p=binding(True); parameters.append(p); inputs[p]=dtype(0)
        output=dtype(0); body=block(0); answer=expr(0)
        require(cursor[0]==len(words),'Trailing grammar words')
        program={'schema':ir.SCHEMA,'parameters':parameters,'inputs':inputs,'output_type':output,'body':body,'return':answer}
        ir.validate(program)
        require(_encode_words(program,profile)==words,'Noncanonical packet')
        return program
    except ir.Invalid as exc:
        raise Invalid(str(exc)) from exc


def execute(packet, positional_inputs, *, budget=100000):
    """Run decoded semantic words through their pinned bounded IR interpreter.

    Arguments are ordered values, not free binding names or source. Each run
    owns fresh runtime resources and copied inputs. This is not a native sandbox.
    """
    require(type(positional_inputs) in (list,tuple),'Ordered positional inputs required')
    require(type(budget) is int and 0<budget<=2000000,'Execution budget must be 1..2000000')
    profile,_,_=_unpack(packet); program=decode(packet); ir=runtime(profile)
    require(len(positional_inputs)==len(program['parameters']),'Positional input arity mismatch')
    arguments=dict(zip(program['parameters'],positional_inputs))
    try:
        return ir.execute(program,arguments,budget=budget)
    except ir.Invalid as exc:
        raise Invalid(str(exc)) from exc
