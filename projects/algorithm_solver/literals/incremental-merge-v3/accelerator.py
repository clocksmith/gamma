"""Trusted exact trie-DP draft; configure pinned owned artifact before loading."""
import ctypes,hashlib
from pathlib import Path
import search
OriginalGraph=search.joint.compact.Graph
LIB=None;IDENTITY=None

def configure(expected_hash,library_path):
 global LIB,IDENTITY
 if not isinstance(expected_hash,str) or len(expected_hash)!=64 or any(c not in '0123456789abcdef' for c in expected_hash):raise ValueError('explicit SHA256 required')
 path=Path(library_path).resolve()
 if hashlib.sha256(path.read_bytes()).hexdigest()!=expected_hash:raise ValueError('trie kernel mismatch before CDLL')
 identity=(str(path),expected_hash)
 if IDENTITY is not None:
  if identity!=IDENTITY:raise ValueError('trie kernel reconfiguration forbidden')
  return LIB
 lib=ctypes.CDLL(str(path))
 lib.gamma_trie_build.argtypes=[ctypes.POINTER(ctypes.c_char_p),ctypes.POINTER(ctypes.c_int),ctypes.c_int];lib.gamma_trie_build.restype=ctypes.c_void_p
 lib.gamma_trie_free.argtypes=[ctypes.c_void_p];lib.gamma_trie_free.restype=None
 lib.gamma_trie_score.argtypes=[ctypes.c_void_p,ctypes.c_char_p,ctypes.c_int,ctypes.POINTER(ctypes.c_int),ctypes.POINTER(ctypes.c_int),ctypes.POINTER(ctypes.c_int)];lib.gamma_trie_score.restype=ctypes.c_int
 if hashlib.sha256(path.read_bytes()).hexdigest()!=expected_hash:raise ValueError('trie kernel changed during loading')
 LIB,IDENTITY=lib,identity;return lib

class TrieGraph(OriginalGraph):
 def score(self,vocab,previous=None,changed=()):
  if LIB is None:raise RuntimeError('configure required')
  if vocab[:96]!=search.ALPHABET or not 96<=len(vocab)<=256 or len(set(vocab))!=len(vocab) or any(not p for p in vocab):raise ValueError('trie dictionary contract mismatch')
  pieces=[p.encode('ascii') for p in vocab]
  if sum(map(len,pieces))>10000000:raise ValueError('bounded trie dictionary exceeded')
  pointers=(ctypes.c_char_p*len(pieces))(*pieces);lengths=(ctypes.c_int*len(pieces))(*(len(p) for p in pieces))
  handle=LIB.gamma_trie_build(pointers,lengths,len(pieces))
  if not handle:raise ValueError('trie build rejected dictionary/allocation')
  try:
   affected=set(self.texts) if previous is None else set().union(*(set(self.occurrence(p)) for p in changed));rows={} if previous is None else dict(previous)
   for key in affected:
    raw=self.texts[key].encode('ascii')
    if len(raw)>10000000:raise ValueError('bounded source exceeded')
    sequence=(ctypes.c_int*max(1,len(raw)))();count=ctypes.c_int();chars=ctypes.c_int()
    code=LIB.gamma_trie_score(handle,raw,len(raw),sequence,ctypes.byref(count),ctypes.byref(chars))
    if code:raise ValueError('trie score status '+str(code))
    used=[vocab[sequence[i]] for i in range(count.value)];positions=[];at=0
    for p in used:
     if len(p)==1:positions.append(at)
     at+=len(p)
    if at!=len(raw) or len(positions)!=chars.value or ''.join(used)!=self.texts[key]:raise ValueError('trie exact reconstruction/count mismatch')
    rows[key]={'selections':count.value,'characters':chars.value,'used':used,'character_positions':positions}
   return rows
  finally:LIB.gamma_trie_free(handle)
