"""Normalize a closed joint-training/replay comparison for the existing recorder.

This creates evidence alongside results. It neither launches jobs nor assigns
scientific verdicts; a validated reflection and record_driver_result remain
required for canonical row publication.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import socket
from gamma_enwiki9.evidence.artifacts import canonical_bytes, fingerprint, publish_immutable_artifact


def normalize(root: Path, candidate: str, job_id: str):
    def ref(path):
        identity = fingerprint(path, root)
        return {k: identity[k] for k in ('path', 'sha256', 'bytes')}
    paths = list((root / 'operations/adaptive/completed').glob('*_' + job_id + '.json'))
    if len(paths) != 1: raise ValueError('one canonical completed job required')
    job_path = paths[0]; job = json.loads(job_path.read_bytes())
    if job['candidate_id'] != candidate or job['execution_resources'].get('cleanup_complete') is not True:
        raise ValueError('job candidate or completed cleanup differs')
    output = root / 'results' / candidate; native = output / 'native'
    comparison_path = output / 'comparison.json'; comparison = json.loads(comparison_path.read_bytes())
    experiment = json.loads((root / job['experiment']['path']).read_bytes())
    guard_path = root / job['execution_resources']['guard_path']
    guard = json.loads(guard_path.read_bytes())
    if guard.get('status') in (None, 'running') or guard.get('returncode') != 0:
        raise ValueError('successful closed resource guard required')
    raw_path = next(root / row['path'] for row in experiment['inputs']
                    if row['path'].startswith('operations/evidence/fixtures/') and row['path'].endswith('.raw'))
    raw_ref = ref(raw_path)
    revision = {'candidateId': candidate, 'candidateTreeSha256': job['candidate_tree_sha256'],
                'receipt': job['candidate_revision']}
    index = {'schema': 'gamma.enwiki9.terminal-result-index.v1', 'job': ref(job_path),
             'guard': ref(guard_path), 'arms': [], 'evidence': [ref(comparison_path), ref(output / 'artifacts.json')]}
    for arm in ('P', 'E', 'K', 'M', 'S'):
        if arm not in comparison['archive_bytes']: continue
        archive = native / (arm + '.arc'); restored = native / (arm + '.raw'); repeat = native / (arm + '.repeat.arc')
        archive_ref = ref(archive)
        if archive_ref['bytes'] != comparison['archive_bytes'][arm]: raise ValueError('archive size differs')
        artifacts = {'archive': archive_ref}
        inverted = repeated = None
        if restored.exists():
            artifacts['restored'] = ref(restored)
            if artifacts['restored']['sha256'] != raw_ref['sha256']: raise ValueError('inverse differs')
            inverted = True
        if repeat.exists():
            artifacts['repeat'] = ref(repeat)
            if artifacts['repeat']['sha256'] != archive_ref['sha256']: raise ValueError('repeat differs')
            repeated = True
        def execution(name):
            path = native / (arm + '-' + name + '.execution.json')
            return json.loads(path.read_bytes()) if path.exists() else None
        encode, decode = execution('encode'), execution('decode')
        rss_path = native / (arm + '-encode.rusage.json')
        rss = json.loads(rss_path.read_bytes())['maximum_process_rss_kib'] if rss_path.exists() else None
        result = {'schema': 'gamma.enwiki9.driver-result.v2', 'program_id': candidate,
                  'program_name': 'Native FX2 joint data/model training and title conditioning',
                  'arm': arm, 'candidate_revision': revision, 'timestamp': job['finished_at'],
                  'data_path': raw_ref['path'], 'data_size': raw_ref['bytes'], 'data_sha256': raw_ref['sha256'],
                  'compressed_size': archive_ref['bytes'], 'compressed_sha256': archive_ref['sha256'],
                  'compressed_md5': hashlib.md5(archive.read_bytes()).hexdigest(),
                  'bits_per_byte': archive_ref['bytes'] * 8 / raw_ref['bytes'],
                  'roundtrip_ok': inverted, 'determinism': {'single_host_byte_equal': repeated},
                  'compress_time_s': encode['elapsed_seconds'] if encode else None,
                  'decompress_time_s': decode['elapsed_seconds'] if decode else None,
                  'memory_kib': {'peak': rss},
                  'memory_scope': 'native encode maximum process RSS when available; aggregate job cgroup peak is separately bound',
                  'packed_model_bytes': comparison['packed_model_bytes'][arm], 'planning_model_copies': 2,
                  'program_size': None, 'hutter_score': None, 'complete_package_bytes': None,
                  'full_corpus_score_bytes': None, 'score_accounting_complete': False, 'prize_claimable': False,
                  'qualification_status': 'not-certified', 'discovery_resource_gate_pass': True,
                  'resource_evidence_complete': False, 'objective_credit_bytes': 0,
                  'run_purpose': 'diagnostic', 'run_scope_label': str(raw_ref['bytes']) + '-joint-model-' + arm,
                  'run_source': job_path.relative_to(root).as_posix(),
                  'run_context': 'Fixed native model and population. Missing per-arm operations remain null; no package or full-corpus score inferred. See source comparison for exact controls and prior evidence.',
                  'run_tags': ['joint-model-training', 'native-archive', 'zero-score-credit', arm],
                  'host': {'hostname': socket.gethostname()}, 'source_terminal': ref(comparison_path),
                  'missing_diagnostics': ['complete submission packaging and full parent-state/isolated resource qualification are unavailable']}
        if inverted is None or repeated is None:
            result['missing_diagnostics'].append('inverse/repeat not independently executed for this arm in this job; prior evidence is not relabeled as a fresh operation')
        if rss is None: result['missing_diagnostics'].append('per-arm peak RSS unavailable; bound guard records aggregate job peak')
        path = output / (arm + '.driver.json')
        publish_immutable_artifact(path, canonical_bytes(result) + b'\n')
        index['arms'].append({'arm': arm, 'result': ref(path), 'artifacts': artifacts})
    path = output / 'terminal-index.json'
    publish_immutable_artifact(path, canonical_bytes(index) + b'\n')
    return ref(path)
