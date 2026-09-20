"""Assemble explicitly supplied delivery members; no experiment discovery."""
from pathlib import Path
import struct


def assemble(wrapper: Path, codec: Path, dictionary: Path, weights: Path, destination: Path):
    import shutil
    paths=[wrapper,codec,dictionary,weights]
    if any(p.is_symlink() or not p.is_file() or not 0<p.stat().st_size<=2_000_000_000 for p in paths):
        raise ValueError('invalid explicit delivery member')
    sizes=[p.stat().st_size for p in paths]
    with destination.open('xb') as sink:
        for path in paths:
            with path.open('rb') as source:shutil.copyfileobj(source,sink,1<<20)
        sink.write(struct.pack('<8s8Q',b'GFX2PK01',0,*sizes,0,0,0))
    destination.chmod(0o755)
    return {'format':'GFX2PK01','footer_bytes':72,'member_bytes':dict(zip(('wrapper','codec','dictionary','weights'),sizes)),
            'compressor_bytes':destination.stat().st_size,'decoder':'No arguments; writes enwik9 in current directory without replacement.',
            'internal_integrity':'FNV-1a64 and exact size, not cryptographic authentication; evidence manifests supply SHA256.',
            'profile':'Existing native -c/-d frontend with explicit dictionary and transformer weights; no full-corpus reorder/split pipeline.'}
