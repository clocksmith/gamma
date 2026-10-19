"""Offline representation experiment. No inference, execution, or source lookup in decoder."""
import hashlib,json,re
from collections import Counter,defaultdict
MAGIC=b'CMA1';IDENT=re.compile(r'^[A-Za-z_$][A-Za-z0-9_$]*$')
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def uvar(n):
 if not isinstance(n,int) or n<0:raise ValueError('unsigned integer required')
 out=bytearray()
 while n>=128:out.append((n&127)|128);n>>=7
 out.append(n);return bytes(out)
def readvar(data,pos):
 start=pos;n=shift=0
 for _ in range(5):
  if pos>=len(data):raise ValueError('truncated operand')
  b=data[pos];pos+=1;n|=(b&127)<<shift
  if b<128:
   if data[start:pos]!=uvar(n):raise ValueError('noncanonical varint')
   return n,pos
  shift+=7
 raise ValueError('operand too long')
def template(text,names):
 # Only reviewed no-string/no-comment fragment shapes enter this builder.
 lines=text.splitlines();indent=min((len(x)-len(x.lstrip(' ')) for x in lines[1:] if x.strip()),default=0)
 # The terminal closing brace sits at base indentation for JS; Python body is base+4.
 base=indent if lines[-1].strip()=='}' else indent-4
 assert base>=0
 normalized=lines[0]+''.join('\n'+line[base:] for line in lines[1:])
 pattern=re.compile(r'\b(?:'+ '|'.join(re.escape(n) for n in sorted(names,key=len,reverse=True))+r')\b')
 parts=[];last=0
 for m in pattern.finditer(normalized):
  parts.extend([normalized[last:m.start()],names.index(m.group())]);last=m.end()
 parts.append(normalized[last:]);return dict(parts=parts,arity=len(names)),base

def expand(variant,bindings,operands,indent):
 if not 0<=indent<=64 or len(operands)!=variant['arity'] or len(set(operands))!=len(operands):raise ValueError('invalid binding/indent')
 if any(i>=len(bindings) for i in operands):raise ValueError('unknown binding')
 text=''.join(bindings[operands[v]] if isinstance(v,int) else v for v in variant['parts'])
 return text.replace('\n','\n'+' '*indent).encode()

def lexical(texts,count):
 words=Counter(t for text in texts for t in re.findall(r'[A-Za-z_$][A-Za-z_0-9$]+|\n +| {2,}|===|!==|==|!=|<=|>=|//|\*\*|:=|->|\+=|-=|=>',text))
 return sorted(words,key=lambda t:(-words[t]*(len(t.encode())-1),t))[:count]
def book(language,kind,texts,fragments=None):
 entries=[dict(id=0,kind='end'),dict(id=1,kind='literal_run',length='uvarint32',body='utf8 bytes')]
 if kind=='whole':entries += [dict(id=i+2,kind='whole',body=text) for i,text in enumerate(texts)]
 else:
  entries += [dict(id=i+2,kind='text',body=chr(i)) for i in range(128)]
  count=124 if kind=='semantic' else 126
  entries += [dict(id=i+130,kind='text',body=t) for i,t in enumerate(lexical(texts,count))]
  if kind=='semantic':entries += [dict(id=254+i,kind='fragment',**f) for i,f in enumerate(fragments)]
 assert len(entries)<=256 and len({e['id'] for e in entries})==len(entries)
 return dict(schema='corpus-macro-codebook-v1',language=language,kind=kind,max_slots=256,stream_header='CMA1, language byte, profile byte,32-byte codebook SHA256, binding count, UTF8 length-prefixed identifiers',operand_encoding='fragment variant byte, indentation uvarint, one uvarint slot reference per fixed-arity identifier operand; fixed constants and operators live in the charged codebook',control='END required; unknown IDs and malformed operands fail closed',entries=entries)
def frame(b,bindings):
 out=bytearray(MAGIC+bytes([0 if b['language']=='javascript' else 1,{'lexical':0,'semantic':1,'whole':2}[b['kind']]])+hashlib.sha256(canonical(b)).digest()+uvar(len(bindings)))
 for name in bindings:
  raw=name.encode();out+=uvar(len(raw))+raw
 return bytes(out)
def decode(data,b):
 if len(data)>1000000 or data[:38]!=frame(b,[])[:38]:raise ValueError('wrong profile or header')
 count,p=readvar(data,38)
 if count>256:raise ValueError('too many bindings')
 bindings=[]
 for _ in range(count):
  length,p=readvar(data,p)
  if length>128 or p+length>len(data):raise ValueError('binding length')
  name=data[p:p+length].decode();p+=length
  if not IDENT.fullmatch(name) or name in bindings:raise ValueError('binding name')
  bindings.append(name)
 entries={e['id']:e for e in b['entries']};out=bytearray()
 while p<len(data):
  code=data[p];p+=1;e=entries.get(code)
  if e is None:raise ValueError('unknown macro')
  if e['kind']=='end':
   if p!=len(data):raise ValueError('trailing input')
   return bytes(out)
  if e['kind']=='literal_run':
   length,p=readvar(data,p)
   if p+length>len(data):raise ValueError('truncated literal')
   out+=data[p:p+length];p+=length
  elif e['kind'] in ['text','whole']:out+=e['body'].encode()
  else:
   if p>=len(data):raise ValueError('missing variant')
   variant=data[p];p+=1
   if variant>=len(e['variants']):raise ValueError('invalid variant')
   indent,p=readvar(data,p);operands=[]
   for _ in range(e['variants'][variant]['arity']):v,p=readvar(data,p);operands.append(v)
   out+=expand(e['variants'][variant],bindings,operands,indent)
  if len(out)>1000000:raise ValueError('expansion limit')
 raise ValueError('missing end')
def encode(source,b,occurrences=(),whole_index=None):
 raw=source.encode()
 if b['kind']=='whole':return frame(b,[])+bytes([whole_index+2,0]),dict(fragment_uses=0,bindings=0,header_binding_bytes=len(frame(b,[])),body_bytes=1,end_bytes=1,literal_bytes=0,whole_uses=1)
 choices=defaultdict(list)
 for e in b['entries']:
  if e['kind']=='text':choices[e['body'].encode()[0]].append((e['body'].encode(),bytes([e['id']]),None))
 def solve(use):
  bindings=sorted({n for o in occurrences for n in o['names']}) if use else [];positions=defaultdict(list)
  if use:
   for o in occurrences:
    operands=[bindings.index(n) for n in o['names']];token=bytes([o['code'],o['variant']])+uvar(o['indent'])+b''.join(uvar(v) for v in operands)
    positions[o['start']].append((o['text'].encode(),token,o))
  size=len(raw);cost=[10**12]*(size+1);cost[size]=0;path=[None]*size
  for i in range(size-1,-1,-1):
   opts=choices[raw[i]]+positions[i]
   if raw[i]>=128:
    j=i+1
    while j<size and raw[j]>=128:j+=1
    opts=opts+[(raw[i:j],b'\x01'+uvar(j-i)+raw[i:j],None)]
   for text,token,occ in opts:
    if raw.startswith(text,i) and len(token)+cost[i+len(text)]<cost[i]:cost[i]=len(token)+cost[i+len(text)];path[i]=(text,token,occ)
  body=bytearray();used=[];literal=0;i=0
  while i<size:
   if path[i] is None:raise ValueError('unencodable')
   text,token,occ=path[i];body+=token
   if occ:used.append(occ)
   if token[0]==1:literal+=len(text)
   i+=len(text)
  header=frame(b,bindings);return header+body+b'\0',dict(fragment_uses=len(used),fragment_ids=[o['code'] for o in used],bindings=len(bindings),header_binding_bytes=len(header),body_bytes=len(body),end_bytes=1,literal_bytes=literal,whole_uses=0)
 a=solve(False)
 if occurrences:
  z=solve(True)
  if len(z[0])<len(a[0]):return z
 return a
