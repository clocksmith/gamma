"""Export public BITS discovery assets without models, solutions or private gate files."""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
from .bits_recognition import BitsRecognizer
from .embed import QUERY_INSTRUCTION, MAX_TOKENS


def sha(data):
    return hashlib.sha256(data).hexdigest()


def export_bundle(*, public_root, keys, vectors, gate, gate_sha256, doppler_root, output, model_variants):
    public_root, doppler_root, output = map(Path, (public_root, doppler_root, output))
    recognizer = BitsRecognizer(public_root=public_root, keys=keys, vectors=vectors,
                               gate=gate, gate_sha256=gate_sha256,
                               runtime=SimpleNamespace(identity={'operation': 'export-only-no-inference'}))
    output.mkdir(parents=True, exist_ok=True)
    variants = json.loads(Path(model_variants).read_text())
    rows = []
    for key in recognizer.keys:
        meta = recognizer.metadata[key]
        description, scope = recognizer.document(key)
        notices = {'attribution': ['https://leetcode.com/problems/'+meta['slug']+'/'], 'license': []}
        if scope == 'published-statement':
            raw = (recognizer.bits/'problems'/(meta['slug']+'.json')).read_bytes()
            if sha(raw) != recognizer.manifest['problems'][meta['slug']]['sha256']:
                raise ValueError('Public statement changed during export')
            source = json.loads(raw).get('source', {})
            notices = {k: source[k] for k in ('attribution', 'license', 'use', 'corpus_sha256') if k in source}
        rows.append({'key': key, 'slug': meta['slug'], 'title': meta['title'],
                     'problemId': meta['problem_id'], 'difficulty': meta['difficulty'],
                     'aliases': [meta['slug'], meta['title'], meta['problem_id']],
                     'description': description, 'scope': scope,
                     'descriptionSha256': sha(description.encode()), 'notices': notices})
    files = {}
    def emit(name, data):
        (output/name).write_bytes(data)
        files[name] = {'url': name, 'sha256': sha(data), 'bytes': len(data)}
    emit('documents.json', (json.dumps(rows, ensure_ascii=False, separators=(',', ':'))+'\n').encode())
    emit('vectors.f32', recognizer.vectors.astype('<f4').tobytes(order='C'))
    runtime_config = Path(__file__).with_name('config')/'bits-reranker-tiled-v1/runtime-config.json'
    emit('reranker-config.json', runtime_config.read_bytes())
    specs = []
    for role in ('embedding', 'rerank'):
        entry = variants[role]
        raw = Path(entry['manifestPath']).read_bytes()
        if sha(raw) != entry['manifestHash']:
            raise ValueError('Migrated model manifest changed')
        manifest = json.loads(raw)
        if manifest['hashAlgorithm'] != 'sha256':
            raise ValueError('Browser publication requires an independently verified SHA256 artifact variant')
        model_file = 'models/'+role+'/manifest.json'
        (output/'models'/role).mkdir(parents=True, exist_ok=True)
        emit(model_file, raw)
        tokenizer = entry['tokenizer']
        specs.append({'role': role, 'modelId': manifest['modelId'],
                      'weightsBaseUrl': entry['weightsBaseUrl'],
                      'manifest': files[model_file], 'manifestSha256': sha(raw),
                      'manifestVariantId': entry['manifestVariantId'],
                      'weightBytes': sum(s['size'] for s in manifest['shards']),
                      'tokenizerSha256': tokenizer['sha256'],
                      'tokenizerBytes': tokenizer['size']})
    manifest = {'schema': 'gamma.bits-browser-recognition.v1', 'version': 'qwen-known-corpus-v1',
                'dimensions': 1024, 'count': len(rows), 'vectors': files['vectors.f32'],
                'documents': files['documents.json'], 'rerankerConfig': files['reranker-config.json'],
                'models': specs, 'policy': {'queryInstruction': QUERY_INSTRUCTION, 'maxTokens': MAX_TOKENS,
                    'retrievalLimit': 10, 'resultLimit': 3, 'scoring': 'yes-minus-no',
                    'normalization': 'l2', 'tiePolicy': 'abstain', 'recognitionQualified': False},
                'provenance': {'vectorsSha256': sha(Path(vectors).read_bytes()),
                    'keysSha256': sha(Path(keys).read_bytes()),
                    'publicPacketsSha256': sha((public_root/'labs/two-button/problems/manifest.json').read_bytes()),
                    'exporterSha256': sha(Path(__file__).read_bytes()),
                    'dopplerRevision': subprocess.check_output(['git', '-C', str(doppler_root), 'rev-parse', 'HEAD'], text=True).strip()},
                'limits': 'Frozen reference document vectors; Doppler query embeddings. Protected and unknown identities have title-only documents. No sources, tests, private gates or solution receipts are included. No population accuracy or cross-device latency qualification.'}
    data = (json.dumps(manifest, indent=2)+'\n').encode()
    (output/'manifest.json').write_bytes(data)
    (output/'release.js').write_text('export const release = '+json.dumps({'sha256': sha(data), 'bytes': len(data)})+';\n')
    return {'manifestSha256': sha(data), 'count': len(rows),
            'statementCount': sum(r['scope'] == 'published-statement' for r in rows),
            'titleOnlyCount': sum(r['scope'] == 'title-only' for r in rows)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['public-root', 'keys', 'vectors', 'gate', 'doppler-root', 'output', 'model-variants']:
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--gate-sha256', required=True)
    print(json.dumps(export_bundle(**vars(p.parse_args())), indent=2))

if __name__ == '__main__':
    main()
