"""Optional trusted C DP acceleration; it treats solution text only as bytes."""
import ctypes
import hashlib
from pathlib import Path
import search
OriginalGraph=search.joint.compact.Graph
LIBRARY=Path('/workspace/shared/gamma-dot-diagnostics/score_kernel.so')
LIB = None
FN = None
_CONFIGURED = None

def configure(expected_hash, library_path=LIBRARY):
    """Validate explicit frozen artifact identity BEFORE loading any ELF code.

    The caller supplies the successor contract digest. This reads an owned,
    trusted compiler artifact; candidate programs are never executable inputs.
    The active fit must keep that artifact immutable. Reconfiguration to another
    identity in the same process is rejected.
    """
    global LIB, FN, _CONFIGURED
    if not isinstance(expected_hash,str) or len(expected_hash)!=64 or any(c not in '0123456789abcdef' for c in expected_hash):
        raise ValueError('explicit lowercase SHA256 required before CDLL')
    library=Path(library_path).resolve()
    raw=library.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected_hash:
        raise ValueError('kernel identity mismatch before CDLL')
    identity=(str(library),expected_hash)
    if _CONFIGURED is not None:
        if _CONFIGURED!=identity:raise ValueError('kernel reconfiguration forbidden')
        return LIB
    lib=ctypes.CDLL(str(library))
    fn=lib.gamma_score
    fn.argtypes=[ctypes.c_char_p,ctypes.c_int,ctypes.POINTER(ctypes.c_char_p),ctypes.POINTER(ctypes.c_int),ctypes.c_int,ctypes.POINTER(ctypes.c_int),ctypes.POINTER(ctypes.c_int),ctypes.POINTER(ctypes.c_int)]
    fn.restype=ctypes.c_int
    # Detect accidental artifact replacement during loading too; callers retain
    # the immutable owned-artifact assumption, not a hostile-filesystem claim.
    if hashlib.sha256(library.read_bytes()).hexdigest()!=expected_hash:
        raise ValueError('kernel artifact changed during load')
    LIB,FN,_CONFIGURED=lib,fn,identity
    return LIB

class FastGraph(OriginalGraph):
    def score(self,vocab,previous=None,changed=()):
        if FN is None:raise RuntimeError('configure(expected_hash) required before scoring')
        if vocab[:96]!=search.ALPHABET or not 96<=len(vocab)<=256:raise ValueError('kernel alphabet/capacity mismatch')
        if len(set(vocab))!=len(vocab) or any(not s for s in vocab):raise ValueError('invalid literal entries')
        pieces=[s.encode('ascii') for s in vocab]
        pointers=(ctypes.c_char_p*len(vocab))(*pieces)
        lengths=(ctypes.c_int*len(vocab))(*(len(s) for s in pieces))
        affected=set(self.texts) if previous is None else set().union(*(set(self.occurrence(p)) for p in changed))
        rows={} if previous is None else dict(previous)
        for key in affected:
            raw=self.texts[key].encode('ascii')
            if len(raw)>10000000:raise ValueError('source exceeds bounded kernel input')
            sequence=(ctypes.c_int*max(1,len(raw)))();count=ctypes.c_int();chars=ctypes.c_int()
            status=FN(raw,len(raw),pointers,lengths,len(vocab),sequence,ctypes.byref(count),ctypes.byref(chars))
            if status:raise ValueError(f'DP kernel status {status}')
            used=[vocab[sequence[i]] for i in range(count.value)];positions=[];at=0
            for piece in used:
                if len(piece)==1:positions.append(at)
                at+=len(piece)
            if at!=len(raw) or len(positions)!=chars.value or ''.join(used)!=self.texts[key]:raise ValueError('kernel reconstruction/count mismatch')
            rows[key]={'selections':count.value,'characters':chars.value,'used':used,'character_positions':positions}
        return rows
