"""Parallel tree slots for the frozen typed IR, fitted on development-fit only.

Every statement, primitive expression and explicit reference has its own slot.
First-child/next-sibling edges describe control flow and operand order. Binding
indices address inputs or declaration slots. Recipes stay inspectable IR calls.
Integer parameters use sign plus 128 magnitude bits, not expression templates.
"""
from __future__ import annotations

import json
import math

from . import typed_program as ir, typed_recipes, typed_codec

INPUTS = 8
BITS = ir.MAX_INTEGER_BITS + 1
OPS = ['EMPTY', 'root', 'sequence', 'let', 'var', 'set', 'for', 'if', 'ref', 'int', 'bool']
OPS += ['pure:'+x for x in sorted(ir.PURE)]
OPS += ['call:'+x for x in sorted(ir.EFFECTS)]
OPS += ['recipe:'+x for x in sorted(typed_recipes.catalog())]


def flatten(program):
    ir.validate(program, typed_recipes.catalog())
    if len(program['parameters']) > INPUTS:
        raise ValueError('Too many prediction inputs')
    nodes=[]
    def new(op, binding=-100, value=None):
        index=len(nodes)
        bits=[-100]*BITS
        if value is not None:
            bits=[int(value < 0)] + [(abs(int(value)) >> b) & 1 for b in range(BITS-1)]
        nodes.append({'op':OPS.index(op),'first':0,'next':0,'binding':binding,'bits':bits})
        return index
    def children(parent, indices):
        if indices:
            nodes[parent]['first']=indices[0]+1
            for left,right in zip(indices,indices[1:]): nodes[left]['next']=right+1
    def expr(value,scope):
        if 'ref' in value: return new('ref',scope[value['ref']])
        if 'literal' in value: return new('bool' if type(value['literal']) is bool else 'int',value=value['literal'])
        index=new('pure:'+value['op']); children(index,[expr(a,scope) for a in value['args']]); return index
    def sequence(body,scope):
        index=new('sequence'); items=[]
        for statement in body:
            op=statement['op']
            label='call:'+statement['operator'] if op=='call' else 'recipe:'+statement['recipe'] if op=='recipe' else op
            slot=new(label); items.append(slot)
            if op in ('let','var','set'):
                children(slot,[expr(statement['value'],scope)])
                if op=='set': nodes[slot]['binding']=scope[statement['name']]
                else: scope[statement['name']]=INPUTS+slot
            elif op in ('call','recipe'):
                children(slot,[expr(a,scope) for a in statement['args']]); scope[statement['out']]=INPUTS+slot
            elif op=='for':
                values=expr(statement['in'],scope)
                body=sequence(statement['body'],{**scope,statement['item']:INPUTS+slot})
                children(slot,[values,body])
            elif op=='if':
                children(slot,[expr(statement['condition'],scope),sequence(statement['then'],dict(scope)),sequence(statement['else'],dict(scope))])
        children(index,items); return index
    root=new('root'); scope={name:i for i,name in enumerate(program['parameters'])}
    body=sequence(program['body'],scope); answer=expr(program['return'],scope)
    children(root,[body,answer])
    types=[ir.canonical(ir.dtype(program['inputs'][p])) for p in program['parameters']]
    types.append(ir.canonical(ir.dtype(program['output_type'])))
    return nodes,types


class PredictionCodec:
    def __init__(self,slots,types):
        if not 1 <= slots <= ir.MAX_GRAPH_NODES or len(set(types)) != len(types):
            raise ValueError('Invalid prediction vocabulary')
        self.slots=slots; self.types=list(types)

    @classmethod
    def fit(cls,pairs):
        if not pairs or any(p['learning_split']!='development_fit' for p in pairs):
            raise ValueError('Prediction encoding may use development_fit only')
        flattened=[flatten(p['target']['program']) for p in pairs]
        slots=64*math.ceil(max(len(nodes) for nodes,_ in flattened)/64)
        return cls(slots,sorted({t for _,ts in flattened for t in ts}))

    def descriptor(self):
        return {'schema':'algsolve.typed-prediction.v1','slots':self.slots,'types':self.types,
                'operators':OPS,'input_slots':INPUTS,'literal_bits':BITS,
                'structure':'preorder first-child/next-sibling tree; all slots predicted in parallel',
                'bindings':'input index or 8 + declaration slot; validator enforces lexical scope',
                'target':'frozen typed IR, no arbitrary expression holes'}

    def encode(self,program):
        nodes,types=flatten(program)
        if len(nodes)>self.slots: raise ValueError('Prediction slot budget exceeded')
        result={k:[] for k in ('op','first','next','binding','bits')}
        for node in nodes:
            for k in result: result[k].append(node[k])
        for _ in range(self.slots-len(nodes)):
            for k in result: result[k].append(0 if k=='op' else [-100]*BITS if k=='bits' else -100)
        result['types']=[-100]*(INPUTS+1)
        for i,t in enumerate(types[:-1]): result['types'][i]=self.types.index(t)
        result['types'][INPUTS]=self.types.index(types[-1])
        return result

    def decode(self,codes,params):
        if len(params)>INPUTS or len(set(params))!=len(params): raise ValueError('Invalid inputs')
        if any(len(codes[k])!=self.slots for k in ('op','first','next','binding','bits')) or len(codes['types'])!=INPUTS+1:
            raise ValueError('Prediction dimensions differ')
        def op(i):
            v=int(codes['op'][i])
            if not 0<=v<len(OPS): raise ValueError('Invalid operation')
            return OPS[v]
        active=[i for i in range(self.slots) if op(i)!='EMPTY']
        if not active or active != list(range(len(active))) or op(0)!='root' or int(codes['next'][0])!=0:
            raise ValueError('Invalid root or nontrailing empty slots')
        used={0}
        def children(i):
            result=[]; pointer=int(codes['first'][i])
            while pointer:
                child=pointer-1
                if child<=i or child>=len(active) or child in used:
                    raise ValueError('Invalid, shared or cyclic tree edge')
                used.add(child); result.append(child); pointer=int(codes['next'][child])
            return result
        names={i:p for i,p in enumerate(params)}
        def declaration(i):
            name=f'slot_{i}'
            if name in params: raise ValueError('Declaration collides with parameter')
            names[INPUTS+i]=name
            return name
        def binding(i):
            v=int(codes['binding'][i])
            if v not in names: raise ValueError('Binding has no preceding declaration')
            return names[v]
        def expr(i):
            label=op(i); cs=children(i)
            if label=='ref' and not cs: return {'ref':binding(i)}
            if label in ('int','bool') and not cs:
                bits=[int(v) for v in codes['bits'][i]]
                if len(bits)!=BITS or any(b not in (0,1) for b in bits): raise ValueError('Invalid literal bits')
                v=sum(b<<k for k,b in enumerate(bits[1:])); v=-v if bits[0] else v
                if label=='bool' and (bits[0] or v not in (0,1)): raise ValueError('Invalid Boolean')
                return {'literal':bool(v) if label=='bool' else v}
            if label.startswith('pure:'): return {'op':label[5:],'args':[expr(c) for c in cs]}
            raise ValueError('Expected expression')
        def sequence(i):
            if op(i)!='sequence': raise ValueError('Expected statement sequence')
            statements=[]
            for slot in children(i):
                label=op(slot); cs=children(slot)
                if label in ('let','var','set') and len(cs)==1:
                    value=expr(cs[0]); name=binding(slot) if label=='set' else declaration(slot)
                    statement={'op':label,'name':name,'value':value}
                elif label.startswith(('call:','recipe:')):
                    args=[expr(c) for c in cs]; name=declaration(slot); kind,value=label.split(':',1)
                    statement={'op':kind,'operator' if kind=='call' else 'recipe':value,'out':name,'args':args}
                elif label=='for' and len(cs)==2:
                    values=expr(cs[0]); name=declaration(slot)
                    statement={'op':'for','item':name,'in':values,'body':sequence(cs[1])}
                elif label=='if' and len(cs)==3:
                    statement={'op':'if','condition':expr(cs[0]),'then':sequence(cs[1]),'else':sequence(cs[2])}
                else: raise ValueError('Invalid statement shape')
                statements.append(statement)
            return statements
        root=children(0)
        if len(root)!=2: raise ValueError('Root needs body and return')
        body=sequence(root[0]); answer=expr(root[1])
        if used!=set(active): raise ValueError('Unreachable active nodes')
        def typ(i):
            code=int(codes['types'][i])
            if not 0<=code<len(self.types): raise ValueError('Invalid type code')
            return json.loads(self.types[code])
        program={'schema':ir.SCHEMA,'parameters':params,'inputs':{p:typ(i) for i,p in enumerate(params)},
                 'body':body,'return':answer,'output_type':typ(INPUTS)}
        # Reject out-of-scope references, unsupported ports, resource escape and
        # invalid control flow; decoding never repairs a malformed prediction.
        typed_codec.encode(program,'validation-only')
        return program
