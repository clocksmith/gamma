"""Verify local/dependency/predecessor pins without importing the guard."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def verify():
    freeze=json.loads((HERE/'freeze.json').read_text())
    for name,digest in freeze['files'].items():
        if sha(HERE/name)!=digest:raise ValueError('local implementation/evidence drift: '+name)
    for name,digest in freeze['dependency_code_sha256'].items():
        if sha(HERE.parent/name)!=digest:raise ValueError('imported dependency drift: '+name)
    for key in ('predecessor','independent_review_receipt'):
        pin=freeze[key]
        if sha(pin['path'])!=pin['sha256']:raise ValueError('predecessor/review identity drift')
    return {'status':'pins_verified','freeze_sha256':sha(HERE/'freeze.json'),'recognition_qualified':False}

if __name__=='__main__':print(json.dumps(verify(),sort_keys=True))
