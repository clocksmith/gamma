"""Bounded JS/Python semantic-macro foundation, not a selected 256-entry vocabulary.

The first twelve entries are explicit; 244 slots remain reserved. Both profiles
currently share concepts but have independent language IDs and native expansions.
No arbitrary source payload, graph dependency, inference, or answer lookup.
"""
import json
import keyword
import re

VERSION = 1
MAX_INTEGER = 2**53-1
MAX_INSTRUCTIONS = 256
MAX_STREAM = 65536
LANGUAGES = {'python':0, 'javascript':1}
# o = new output binding, b = existing binding, e = typed ref/literal operand.
ENTRIES = [
    ('new_map','o'), ('var_int','oe'), ('for_each','oe'),
    ('map_get','obee'), ('add','oee'), ('assign','be'),
    ('map_set','obee'), ('return','e'), ('end',''),
    ('empty_list','o'), ('if_equal','ee'), ('append','oee'),
]
BY_NAME = {name:(i,fields) for i,(name,fields) in enumerate(ENTRIES)}
RESERVED_WORDS = set('break case catch class const continue debugger default delete do else enum export extends false finally for function if import in instanceof let new null return super switch this throw true try typeof var void while with yield await implements interface package private protected public static'.split())

# Function declarations must not shadow emitted JS dependencies or violate strict bindings.
# Python methods live on Solution and do not shadow these module/global names.
JS_METHOD_COLLISIONS = frozenset({'addInt','Map','Number','Array','RangeError','TypeError','eval','arguments'})


def require(condition,message):
    if not condition:raise ValueError(message)


def slot(value):
    require(type(value) is int and 0<=value<256,'Binding must be one byte')
    return value


def integer(value):
    require(type(value) is int and abs(value)<=MAX_INTEGER,'Integer outside exact shared Number domain')
    return value


def check_record(record):
    require(set(record)=={'schema','language','method','instructions'},'Unexpected macro program fields')
    require(record['schema']=='algsolve.semantic-macros.v1','Unknown macro profile')
    require(record['language'] in LANGUAGES,'Unknown source language')
    name=record['method']
    require(isinstance(name,str) and re.fullmatch('[A-Za-z][A-Za-z0-9_]{0,63}',name) and not keyword.iskeyword(name) and name not in RESERVED_WORDS,'Invalid shared function name')
    require(record['language']!='javascript' or name not in JS_METHOD_COLLISIONS,'JavaScript function name conflicts with emitted runtime or strict binding')
    instructions=record['instructions']
    require(isinstance(instructions,list) and 0<len(instructions)<=MAX_INSTRUCTIONS,'Instruction limit')
    for item in instructions:
        require(isinstance(item,dict) and set(item)=={'op','args'} and item['op'] in BY_NAME,'Unknown macro')
        fields=BY_NAME[item['op']][1]
        require(isinstance(item['args'],list) and len(item['args'])==len(fields),'Wrong operand count')
        for kind,arg in zip(fields,item['args']):
            if kind!='e':slot(arg)
            else:
                require(isinstance(arg,dict) and len(arg)==1 and set(arg)<= {'ref','int'},'Unknown operand tag')
                if 'ref' in arg:slot(arg['ref'])
                else:integer(arg['int'])


def expand(record):
    """Validate a lexical scope stack and deterministically emit native source."""
    check_record(record)
    js=record['language']=='javascript';method=record['method']
    scopes=[{0:('list_int',False)}];blocks=[];body=[];returned=False
    def name(n):return 'p0' if n==0 else f'v{n}'
    def expression(e):
        if 'int' in e:return str(e['int']),'int'
        n=e['ref'];require(n in scopes[-1],'Unbound or out-of-scope reference')
        ty=scopes[-1][n][0];require(ty not in ('map','unit'),'Resource/unit is not a value operand')
        return name(n),ty
    def bind(n,ty,mutable=False):
        require(n not in scopes[-1],'Shadowing a live binding is forbidden')
        scopes[-1][n]=(ty,mutable)
    def line(text):body.append('  '*len(scopes)+text if js else '    '*(len(scopes)+1)+text)
    def declaration(n,ty,text,mutable=False):
        bind(n,ty,mutable);line((('let ' if mutable else 'const ')+name(n)+' = '+text+';') if js else name(n)+' = '+text)
    for item in record['instructions']:
        require(not returned,'Instructions after return')
        op=item['op'];a=item['args']
        if op=='end':
            require(bool(blocks),'Unmatched block close')
            if not js and len(body)==blocks[-1]:line('pass')
            blocks.pop();scopes.pop()
            if js:line('}')
        elif op=='new_map':declaration(a[0],'map','new Map()' if js else '{}')
        elif op=='empty_list':declaration(a[0],'list_int','[]',True)
        elif op=='var_int':
            value,ty=expression(a[1]);require(ty=='int','Integer initializer required');declaration(a[0],'int',value,True)
        elif op in ('add','append'):
            left,lt=expression(a[1]);right,rt=expression(a[2])
            require((lt,rt)==(('int','int') if op=='add' else ('list_int','int')),'Operand type mismatch')
            value=f'addInt({left}, {right})' if op=='add' else (f'[...{left}, {right}]' if js else f'{left} + [{right}]')
            declaration(a[0],'int' if op=='add' else 'list_int',value)
        elif op=='assign':
            value,ty=expression(a[1]);require(scopes[-1].get(a[0])==(ty,True),'Assignment requires matching mutable binding')
            line(name(a[0])+' = '+value+(';' if js else ''))
        elif op in ('map_get','map_set'):
            require(scopes[-1].get(a[1])==('map',False),'Map handle required')
            key,kt=expression(a[2]);value,vt=expression(a[3]);require(kt==vt=='int','Map integer ports required')
            target=name(a[1])
            if op=='map_get':declaration(a[0],'int',f'({target}.get({key}) ?? {value})' if js else f'{target}.get({key}, {value})')
            else:
                bind(a[0],'unit')
                line(f'const {name(a[0])} = ({target}.set({key}, {value}), null);' if js else f'{target}[{key}] = {value}')
                if not js:line(f'{name(a[0])} = None')
        elif op in ('for_each','if_equal'):
            require(len(scopes)<16,'Block depth limit')
            if op=='for_each':
                value,ty=expression(a[1]);require(ty=='list_int','Loop needs integer list')
                require(a[0] not in scopes[-1],'Loop cannot shadow a live binding')
                line(f'for (const {name(a[0])} of {value}) {{' if js else f'for {name(a[0])} in {value}:')
            else:
                left,lt=expression(a[0]);right,rt=expression(a[1]);require(lt==rt=='int','Equality requires integers')
                line(f'if ({left} === {right}) {{' if js else f'if {left} == {right}:')
            scopes.append(dict(scopes[-1]));blocks.append(len(body))
            if op=='for_each':bind(a[0],'int')
        elif op=='return':
            require(len(scopes)==1,'Return must close every block')
            value,ty=expression(a[0]);require(ty=='int','First profile returns an integer')
            line('return '+value+(';' if js else ''));returned=True
    require(returned and not blocks,'Missing return or unclosed block')
    if js:
        prefix=f"function addInt(a, b) {{\n  const result = a + b;\n  if (!Number.isSafeInteger(result)) throw new RangeError('integer overflow');\n  return result;\n}}\nfunction {method}(p0) {{\n  if (!Array.isArray(p0) || p0.length > 20000 || p0.some(x => !Number.isSafeInteger(x))) throw new TypeError('bounded integer list required');\n"
        return prefix+'\n'.join(body)+'\n}\n'
    prefix="def addInt(a, b):\n    result = a + b\n    if abs(result) > 9007199254740991:\n        raise ValueError('integer overflow')\n    return result\n\nclass Solution:\n    def "+method+"(self, p0):\n        if type(p0) is not list or len(p0) > 20000 or any(type(x) is not int or abs(x) > 9007199254740991 for x in p0):\n            raise ValueError('bounded integer list required')\n"
    return prefix+'\n'.join(body)+'\n'


def varint(value):
    value=integer(value);n=2*value if value>=0 else -2*value-1;result=[]
    while n>=128:result.append((n&127)|128);n>>=7
    return bytes(result+[n])


def encode(record):
    expand(record)
    method=record['method'].encode('ascii')
    # Explicit version, language and signature: one list[int] parameter -> int.
    data=bytearray(b'M256'+bytes([VERSION,LANGUAGES[record['language']],len(method)])+method+bytes([1,2,0]))
    for item in record['instructions']:
        code,fields=BY_NAME[item['op']];data.append(code)
        for kind,arg in zip(fields,item['args']):
            if kind!='e':data.append(arg)
            elif 'ref' in arg:data.extend([0,arg['ref']])
            else:data.append(1);data.extend(varint(arg['int']))
    require(len(data)<=MAX_STREAM,'Stream too long')
    return bytes(data)


def decode(data):
    require(type(data) is bytes and 10<=len(data)<=MAX_STREAM,'Invalid stream size')
    require(data[:4]==b'M256' and data[4]==VERSION and data[5] in LANGUAGES.values(),'Unknown profile/version/language')
    i=7;n=data[6];require(0<n<=64 and i+n+3<=len(data),'Invalid signature')
    try:method=data[i:i+n].decode('ascii')
    except UnicodeDecodeError as exc:raise ValueError('Non-ASCII function name') from exc
    i+=n;require(data[i:i+3]==bytes([1,2,0]),'Unsupported signature');i+=3
    instructions=[]
    def byte():
        nonlocal i
        require(i<len(data),'Truncated operand');value=data[i];i+=1;return value
    while i<len(data):
        code=byte();require(code<len(ENTRIES),'Reserved macro ID')
        op,fields=ENTRIES[code];args=[]
        for kind in fields:
            if kind!='e':args.append(byte());continue
            tag=byte();require(tag in (0,1),'Unknown operand tag')
            if tag==0:args.append({'ref':byte()});continue
            start=i;value=0
            for shift in range(0,63,7):
                v=byte();value|=(v&127)<<shift
                if v<128:break
            else:raise ValueError('Integer encoding too long')
            value=value//2 if value%2==0 else -(value//2)-1
            require(varint(value)==data[start:i],'Noncanonical integer encoding')
            args.append({'int':value})
        instructions.append({'op':op,'args':args});require(len(instructions)<=MAX_INSTRUCTIONS,'Instruction limit')
    record=dict(schema='algsolve.semantic-macros.v1',language=next(k for k,v in LANGUAGES.items() if v==data[5]),method=method,instructions=instructions)
    expand(record)
    return record


def costs(record):
    data=encode(record);header=10+len(record['method'])
    return dict(macro_selections=len(record['instructions']),header_bytes=header,
                operand_bytes=len(data)-header-len(record['instructions']),
                total_bytes=len(data),total_binary_presses=8*len(data),
                active_entries=len(ENTRIES),reserved_entries=256-len(ENTRIES))


def good_pairs(language,kind):
    r=lambda n:{'ref':n};c=lambda n:{'int':n}
    if kind=='map':
        ops=[('new_map',[1]),('var_int',[2,c(0)]),('for_each',[3,r(0)]),
             ('map_get',[4,1,r(3),c(0)]),('add',[5,r(2),r(4)]),('assign',[2,r(5)]),
             ('add',[6,r(4),c(1)]),('map_set',[7,1,r(3),r(6)]),('end',[]),('return',[r(2)])]
    elif kind=='pair_scan':
        ops=[('empty_list',[1]),('var_int',[2,c(0)]),('for_each',[3,r(0)]),
             ('for_each',[4,r(1)]),('if_equal',[r(3),r(4)]),('add',[5,r(2),c(1)]),
             ('assign',[2,r(5)]),('end',[]),('end',[]),('append',[6,r(1),r(3)]),
             ('assign',[1,r(6)]),('end',[]),('return',[r(2)])]
    else:raise ValueError('Unknown demonstration')
    return dict(schema='algsolve.semantic-macros.v1',language=language,method='numIdenticalPairs',
                instructions=[dict(op=op,args=args) for op,args in ops])
