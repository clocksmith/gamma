"""Read-only exact-path readiness probe; never import/instantiate an encoder.

Only ALGSOLVE_EMBEDDING_DIR is consulted. No scanning, downloads, source/case
loads, NumPy array loads, GPU calls or model imports are performed. Run separately
in the native serving namespace before interpreting local availability.
"""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import stat
import sys

DEFAULT_EMBEDDING_DIR = '/home/x/.local/share/doppler/capsule-baselines/20260906/source-checkpoints/qwen-embedding-source-97b0c614'
EXPECTED_SHA256 = {
    'model.safetensors': '0437e45c94563b09e13cb7a64478fc406947a93cb34a7e05870fc8dcd48e23fd',
    'tokenizer.json': 'def76fb086971c7867b829c23a26261e38d9d74e02139253b38aeb9df8b4b50a',
}
AUXILIARY_FILES = ('config.json', 'tokenizer_config.json', 'special_tokens_map.json')
INDEX_FILES = ('corpus_embeddings.npy', 'corpus_embedding_keys.json',
               'index_embeddings.npy', 'index_embedding_keys.json')
PACKAGES = ('torch', 'transformers', 'numpy', 'safetensors', 'tokenizers')


def _inspect(path, *, hash_bytes=False, maximum_hash_bytes=None):
    result = {'path': str(path)}
    try:
        info = path.stat()
        result.update(exists=True, bytes=info.st_size, regular_file=stat.S_ISREG(info.st_mode))
        if hash_bytes and result['regular_file']:
            if maximum_hash_bytes is not None and info.st_size > maximum_hash_bytes:
                result['hash_status'] = 'size_exceeds_probe_bound'
            else:
                value = hashlib.sha256()
                with path.open('rb') as handle:
                    for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b''):
                        value.update(chunk)
                result.update(sha256=value.hexdigest(), hash_status='computed')
    except OSError as error:
        result.update(exists=False, error=type(error).__name__)
    return result


def inspect_assets(lane_root, *, verify_model_hashes=False):
    override = os.environ.get('ALGSOLVE_EMBEDDING_DIR')
    # Match pinned embed.py exactly: Path(), not expanduser() or another search.
    root = Path(override if override is not None else DEFAULT_EMBEDDING_DIR)
    assets = {}
    for name, expected in EXPECTED_SHA256.items():
        record = _inspect(root / name, hash_bytes=verify_model_hashes)
        record['expected_sha256'] = expected
        record['hash_verified'] = record.get('sha256') == expected
        assets[name] = record
    for name in AUXILIARY_FILES:
        record = _inspect(root / name, hash_bytes=True, maximum_hash_bytes=16_777_216)
        record['expected_sha256'] = None  # Original embed.py pins no auxiliary hashes.
        record['hash_verified'] = False
        assets[name] = record
    indexes = {name: _inspect(Path(lane_root) / 'data' / 'derived' / name)
               for name in INDEX_FILES}
    packages = {}
    for name in PACKAGES:
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    return {'schema': 'gamma.recognition-asset-readiness.v1',
            'public_runtime_commit': '32b0e46bc2909cde11659bc2927737791a4a28a1',
            'embedding_module_blob': 'c78d3de57d6f92bc529dd380603348e5eab0a280',
            'model_repository': 'Qwen/Qwen3-Embedding-0.6B',
            'python_executable': sys.executable, 'python_version': sys.version,
            'embedding_root': str(root),
            'root_resolution': 'ALGSOLVE_EMBEDDING_DIR' if override is not None else 'pinned_default',
            'model_assets': assets, 'index_artifacts': indexes,
            'installed_package_metadata': packages,
            'model_imported': False, 'model_instantiated': False,
            'index_payload_loaded': False, 'candidate_source_reads': 0, 'case_reads': 0,
            'downloads': 0, 'current_serving_release_qualified': False,
            'scope': 'availability in this execution namespace only; auxiliary/runtime/index qualification remains unestablished'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lane-root', required=True, type=Path)
    parser.add_argument('--verify-model-hashes', action='store_true',
                        help='Stream only the two exact model/tokenizer files to verify pinned hashes; no model loading')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    result = inspect_assets(args.lane_root, verify_model_hashes=args.verify_model_hashes)
    text = json.dumps(result, sort_keys=True, indent=2) + '\n'
    if args.output:
        args.output.write_text(text)
    print(text, end='')


if __name__ == '__main__': main()
