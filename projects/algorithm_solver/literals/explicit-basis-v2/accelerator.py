"""Hash-pinned arbitrary UTF8 literal trie with explicit reachability."""
import ctypes,hashlib
from pathlib import Path
LIB=None;IDENTITY=None

def configure(expected,path):
 global LIB,IDENTITY
 path=Path(path).resolve()
 if len(expected)!=64 or any(c not in '0123456789abcdef' for c in expected) or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise ValueError('kernel hash mismatch before CDLL')
 identity=(str(path),expected)
 if IDENTITY is not None:
  if identity!=IDENTITY:raise ValueError('kernel reconfiguration forbidden')
  return
 lib=ctypes.CDLL(str(path));ptr=ctypes.POINTER(ctypes.c_int)
 lib.gamma_trie_build.argtypes=[ctypes.POINTER(ctypes.c_char_p),ptr,ptr,ctypes.c_int];lib.gamma_trie_build.restype=ctypes.c_void_p
 lib.gamma_trie_free.argtypes=[ctypes.c_void_p];lib.gamma_trie_free.restype=None
 lib.gamma_trie_score.argtypes=[ctypes.c_void_p,ctypes.c_char_p,ctypes.c_int,ptr,ptr,ptr];lib.gamma_trie_score.restype=ctypes.c_int
 if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise ValueError('kernel changed during loading')
 LIB,IDENTITY=lib,identity

class Graph:
 def __init__(self,texts):self.texts=texts;self.occ={}
 def occurrence(self,piece):
  if not piece:raise ValueError('empty literal')
  if piece not in self.occ:
   found={}
   for key,text in self.texts.items():
    at=text.find(piece);positions=[]
    while at>=0:positions.append(at);at=text.find(piece,at+1)
    if positions:found[key]=positions
   self.occ[piece]=found
  return self.occ[piece]
 def score(self,vocab,previous=None,changed=(),*,materialize=False):
  if LIB is None:raise RuntimeError('configure required')
  if not 1<=len(vocab)<=256 or any(type(p) is not str or not p for p in vocab) or len(set(vocab))!=len(vocab):raise ValueError('invalid explicit basis')
  pieces=[p.encode('utf8') for p in vocab]
  if sum(map(len,pieces))>10000000:raise ValueError('bounded vocabulary exceeded')
  n=len(pieces);pointers=(ctypes.c_char_p*n)(*pieces);lengths=(ctypes.c_int*n)(*(len(p) for p in pieces));single=(ctypes.c_int*n)(*(int(len(p)==1) for p in vocab))
  handle=LIB.gamma_trie_build(pointers,lengths,single,n)
  if not handle:raise ValueError('kernel dictionary/allocation rejected')
  try:
   affected=set(self.texts) if previous is None else set().union(*(set(self.occurrence(p)) for p in changed));rows={} if previous is None else dict(previous)
   for key in affected:
    raw=self.texts[key].encode('utf8')
    if len(raw)>10000000:raise ValueError('bounded source exceeded')
    sequence=(ctypes.c_int*max(1,len(raw)))();count=ctypes.c_int();chars=ctypes.c_int()
    status=LIB.gamma_trie_score(handle,raw,len(raw),sequence,ctypes.byref(count),ctypes.byref(chars))
    if status==1:rows[key]=None;continue
    if status!=0:raise ValueError('explicit basis score status '+str(status))
    row={'selections':count.value,'characters':chars.value}
    if materialize:
     used=[vocab[sequence[i]] for i in range(count.value)];positions=[];at=0
     for p in used:
      if len(p)==1:positions.append(at)
      at+=len(p)
     if ''.join(used)!=self.texts[key] or len(positions)!=chars.value:raise ValueError('exact trace/count mismatch')
     row.update(used=used,character_positions=positions)
    rows[key]=row
   return rows
  finally:LIB.gamma_trie_free(handle)
 def materialize(self,vocab,rows):
  full=self.score(vocab,materialize=True)
  if set(full)!=set(rows):raise ValueError('row population drift')
  for k,r in full.items():
   old=rows[k]
   if (r is None)!=(old is None) or r is not None and (r['selections'],r['characters'])!=(old['selections'],old['characters']):raise ValueError('reachability/count drift')
  return full
