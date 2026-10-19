"""Approved, pinned recognition reconstruction payloads only; no generic fetch."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import time
import urllib.request

MODEL_REV = '97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3'
DATA_REV = '215604aeed660029df7de2fea5a4d7b6ed476a08'
FILES = {
    'encoder/model.safetensors': (1191586416, 'sha256', '0437e45c94563b09e13cb7a64478fc406947a93cb34a7e05870fc8dcd48e23fd'),
    'encoder/tokenizer.json': (11423705, 'sha256', 'def76fb086971c7867b829c23a26261e38d9d74e02139253b38aeb9df8b4b50a'),
    'encoder/config.json': (727, 'git-blob-sha1', 'cef2749ee93607b8f9a58ec72f4f6bfaf874e71d'),
    'encoder/tokenizer_config.json': (9706, 'git-blob-sha1', '7345216a0785dc7086e8c245b2a9d3896ce2b756'),
    'LeetCodeDataset-train.jsonl': (93643427, 'sha256', 'ef7d64d34b092859607c1010bdd23540860a8cfff2ed7aeb0fe82e0ad524919b'),
}


def verify(path, spec):
    size, kind, expected = spec
    if path.stat().st_size != size:
        raise ValueError('Unexpected payload size: '+path.name)
    digest = hashlib.sha256() if kind == 'sha256' else hashlib.sha1()
    if kind == 'git-blob-sha1':
        digest.update(b'blob '+str(size).encode()+b'\0')
    sha = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4*1024*1024), b''):
            digest.update(block); sha.update(block)
    if digest.hexdigest() != expected:
        raise ValueError('Payload identity differs: '+path.name)
    return {'bytes': size, 'sha256': sha.hexdigest(), 'identity': kind+':'+expected}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve(); root.mkdir(parents=True, exist_ok=True)
    manifest = root/'downloads.json'
    expected = {'model_revision': MODEL_REV, 'dataset_revision': DATA_REV,
                'approved_bytes': sum(s[0] for s in FILES.values()),
                'license_notes': ['Qwen: Apache-2.0; public/ungated at metadata check',
                    'LCD: HF Apache-2.0 vs linked GitHub MIT discrepancy retained; third-party problem text; local research only, no redistribution'],
                'files': {}}
    started = time.monotonic()
    for name, spec in FILES.items():
        path = root/name; path.parent.mkdir(exist_ok=True)
        if not path.exists():
            partial = path.with_suffix(path.suffix+'.part')
            prefix = ('https://huggingface.co/Qwen/Qwen3-Embedding-0.6B/resolve/'+MODEL_REV+'/'
                      if name.startswith('encoder/') else
                      'https://huggingface.co/datasets/newfacade/LeetCodeDataset/resolve/'+DATA_REV+'/')
            url = prefix+path.name+'?download=true'
            for attempt in range(3):
                offset = partial.stat().st_size if partial.exists() else 0
                if offset == spec[0]:
                    break
                headers = {'User-Agent':'Gamma-approved-recognition-reconstruction'}
                if offset: headers['Range'] = f'bytes={offset}-'
                try:
                    with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=45) as response:
                        append = offset > 0 and response.status == 206
                        if append and not response.headers.get('Content-Range','').startswith(f'bytes {offset}-'):
                            raise ValueError('Unexpected partial response')
                        count = offset if append else 0
                        with partial.open('ab' if append else 'wb') as out:
                            last = count
                            for block in iter(lambda: response.read(1024*1024), b''):
                                count += len(block)
                                if count > spec[0]: raise ValueError('Response exceeds approved byte count')
                                out.write(block)
                                if count-last >= 32*1024*1024:
                                    print(json.dumps({'file':name,'bytes':count,'total':spec[0],
                                                      'elapsed_seconds':round(time.monotonic()-started,2)}),flush=True)
                                    last = count
                    break
                except (TimeoutError, OSError) as error:
                    print(json.dumps({'file':name,'attempt':attempt+1,'error_type':type(error).__name__}),flush=True)
                    if attempt == 2: raise
            verify(partial, spec)
            os.replace(partial,path)
        expected['files'][name] = verify(path,spec)
        print(json.dumps({'verified':name,**expected['files'][name]}),flush=True)
    expected['download_and_verification_seconds'] = time.monotonic()-started
    if manifest.exists():
        old = json.loads(manifest.read_text())
        if any(old[k] != expected[k] for k in ('model_revision','dataset_revision','approved_bytes','files')):
            raise ValueError('Existing download manifest differs')
    else:
        manifest.write_text(json.dumps(expected,indent=2)+'\n')
    print(json.dumps({'downloaded_and_verified_bytes':expected['approved_bytes'],
                      'elapsed_seconds':expected['download_and_verification_seconds']}),flush=True)


if __name__ == '__main__': main()
