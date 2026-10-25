"""Bounded native CPU adapter diagnostic; authored texts, never recognition scoring.

The earlier four-thread source is separately archived under its historical hash.
This successor uses the reusable adapter with at most two threads and interop one.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import sys
import time

from .cpu_encoder import PinnedCPUEncoder
from .provision_encoder import budget, sha

TEXTS = (
    'Given two integers, return their sum.',
    'Return the characters of a string in reverse order.',
    'Find the largest integer in a nonempty list.',
    'Determine whether a list contains any repeated integer.',
    'Count the vowels in a string containing lowercase English letters.',
    'Return the integers of a list in ascending order.',
)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'encoder', 'cpu'): p.add_argument('--' + name, type=Path, required=True)
    for name in ('encoder-sha256', 'cpu-sha256', 'native-python-sha256'): p.add_argument('--' + name, required=True)
    p.add_argument('--threads', type=int, choices=(1, 2), default=2)
    args = p.parse_args(argv); root = args.root.absolute()
    if sys.version_info[:2] != (3, 13) or Path(sys.prefix).resolve() != (root / 'venv').resolve():
        raise RuntimeError('diagnostic requires the approved native private venv')
    resource.setrlimit(resource.RLIMIT_AS, (8 * 1024 ** 3, 8 * 1024 ** 3))
    resource.setrlimit(resource.RLIMIT_CPU, (120, 125))
    os.environ.update(OPENBLAS_NUM_THREADS=str(args.threads), OMP_NUM_THREADS=str(args.threads),
                      MKL_NUM_THREADS=str(args.threads), PYTHONDONTWRITEBYTECODE='1')
    started = time.perf_counter(); before = budget(root)
    encoder = PinnedCPUEncoder(root / 'model', encoder_manifest=args.encoder,
                               encoder_manifest_sha256=args.encoder_sha256,
                               cpu_manifest=args.cpu, cpu_manifest_sha256=args.cpu_sha256,
                               native_python_sha256=args.native_python_sha256,
                               threads=args.threads, batch_size=2)
    documents = encoder.encode(list(TEXTS)); document_info = encoder.last_request_info
    first_encoded = time.perf_counter()
    queries = encoder.encode(list(TEXTS), query=True); query_info = encoder.last_request_info
    repeated = encoder.encode([TEXTS[0]], query=True)
    import numpy as np
    import torch
    scores = queries @ documents.T
    result = {'schema': 'gamma.native-cpu-adapter-diagnostic.v1', 'status': 'completed',
              'encoder_identity': encoder.identity(), 'smoke_source_sha256': sha(__file__),
              'running_python_sha256': sha(Path(sys.executable).resolve()),
              'python_version': sys.version, 'device': str(next(encoder._model.parameters()).device),
              'dtype': str(next(encoder._model.parameters()).dtype),
              'torch_threads': torch.get_num_threads(), 'torch_interop_threads': torch.get_num_interop_threads(),
              'virtual_memory_limit_bytes': resource.getrlimit(resource.RLIMIT_AS)[0],
              'cpu_seconds_soft_hard': list(resource.getrlimit(resource.RLIMIT_CPU)),
              'external_wall_limit_seconds': 180, 'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              'authored_text_count': len(TEXTS), 'embedding_shape': list(queries.shape),
              'query_norms': np.linalg.norm(queries, axis=-1).tolist(),
              'diagnostic_nearest_document_indices': scores.argmax(axis=-1).tolist(),
              'repeat_max_absolute_difference': float(np.max(np.abs(queries[0] - repeated[0]))),
              'document_request_metadata': document_info, 'query_request_metadata': query_info,
              'query_embedding_sha256': hashlib.sha256(queries.tobytes()).hexdigest(),
              'first_document_batch_seconds': first_encoded - started,
              'total_seconds': time.perf_counter() - started, 'before_disk': before, 'after_disk': budget(root),
              'candidate_source_reads': 0, 'case_reads': 0, 'protected_data_reads': 0,
              'model_downloads_during_smoke': 0, 'training': False,
              'informal_recognition_qualified': False, 'old_calibration_reused': False,
              'scope': 'six independently authored texts; offline CPU adapter diagnostic, no existing or full-corpus index, no recognition release claim'}
    (root / 'native-cpu-adapter-smoke-v1.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps(result, sort_keys=True), flush=True)


if __name__ == '__main__': main()
