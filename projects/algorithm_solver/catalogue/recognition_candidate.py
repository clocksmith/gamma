"""Pinned incremental embedding candidate; no activation or qualification.

The supervisor is stdlib-only. It enforces a wall deadline by killing its owned
process group and per-process AS/CPU limits. Aggregate RSS is sampled. A required
kernel memory cap must already exist in the process's cgroup-v2 ancestry; the
runner verifies that inherited limit and never creates or changes host policy.
No protected statements, queries, confirmation cohorts or source are inputs.
"""
from __future__ import annotations

import argparse
import array
import ast
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import resource
import signal
import struct
import subprocess
import sys
import tempfile
import time

from . import boundary_policy
from .recognition_inventory import execution_identity

SCHEMA = 'gamma.recognition-candidate-plan.v1'
DIMENSION = 1024
GIB = 1024 ** 3
MAX_BYTES = 64 * 1024 ** 2
CODE_FILES = ('recognition_candidate.py', 'recognition_inventory.py',
              'boundary_policy.py', 'cpu_encoder.py', 'provision_encoder.py')


class CandidateError(ValueError):
    pass


class HardAggregateMemoryUnavailable(CandidateError):
    pass


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 ** 2), b''):
            h.update(chunk)
    return h.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def require(condition, message):
    if not condition:
        raise CandidateError(message)


def _unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate JSON key')
        result[key] = value
    return result


def decode(raw):
    return json.loads(raw, object_pairs_hook=_unique,
        parse_constant=lambda _: (_ for _ in ()).throw(CandidateError('nonfinite JSON')))


def regular_path(path):
    path = Path(path)
    require(path.is_absolute(), 'absolute operator-supplied path required')
    require(not any(p.is_symlink() for p in (path, *path.parents)), 'symlink artifact path')
    require(path.is_file(), 'regular artifact required')
    return path


def pinned(spec):
    require(isinstance(spec, dict) and set(spec) == {'path', 'sha256'}, 'exact artifact descriptor')
    path = regular_path(spec['path'])
    require(path.stat().st_size <= MAX_BYTES, 'artifact metadata size limit')
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == spec['sha256'], 'artifact pin mismatch: ' + str(path))
    return decode(raw)


def atomic_bytes(path, raw):
    """Complete file first, atomic visibility second; caller owns output lock."""
    path = Path(path)
    fd, name = tempfile.mkstemp(prefix='.' + path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def atomic_json(path, value):
    atomic_bytes(path, (json.dumps(value, sort_keys=True, indent=2,
                                  allow_nan=False) + '\n').encode())


def matrix_bytes(rows, dimension=DIMENSION):
    require(isinstance(rows, list) and len(rows) <= 10000, 'bounded vector rows')
    floats = array.array('f')
    for row in rows:
        require(isinstance(row, (list, tuple)) and len(row) == dimension, 'vector dimension')
        require(all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
                    for v in row), 'nonfinite or invalid vector')
        require(abs(math.sqrt(sum(v * v for v in row)) - 1) <= 1e-4, 'vector unit norm')
        floats.extend(row)
    if sys.byteorder != 'little':
        floats.byteswap()
    header = repr({'descr': '<f4', 'fortran_order': False, 'shape': (len(rows), dimension)}).encode('ascii')
    header += b' ' * ((16 - ((10 + len(header) + 1) % 16)) % 16) + b'\n'
    return b'\x93NUMPY\x01\x00' + struct.pack('<H', len(header)) + header + floats.tobytes()


def read_matrix(path, expected_sha256, dimension=DIMENSION):
    path = regular_path(path)
    require(path.stat().st_size <= MAX_BYTES, 'matrix size limit')
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == expected_sha256, 'matrix hash mismatch')
    require(raw[:8] == b'\x93NUMPY\x01\x00' and len(raw) >= 10, 'NPY v1 float32 matrix required')
    length = struct.unpack('<H', raw[8:10])[0]
    require(length <= 4096, 'NPY header bound')
    header = ast.literal_eval(raw[10:10 + length].decode('ascii').strip())
    require(isinstance(header, dict) and set(header) == {'descr', 'fortran_order', 'shape'}, 'NPY header')
    shape = header['shape']
    require(header['descr'] == '<f4' and header['fortran_order'] is False and
            isinstance(shape, tuple) and len(shape) == 2 and type(shape[0]) is int and
            0 <= shape[0] <= 10000 and shape[1] == dimension, 'NPY shape/dtype/order')
    payload = raw[10 + length:]
    require(len(payload) == shape[0] * dimension * 4, 'NPY payload length')
    values = array.array('f')
    values.frombytes(payload)
    if sys.byteorder != 'little':
        values.byteswap()
    rows = [list(values[i:i + dimension]) for i in range(0, len(values), dimension)]
    matrix_bytes(rows, dimension)  # Validate finiteness, dimension and normalization.
    return rows


def vector_hash(row):
    values = array.array('f', row)
    if sys.byteorder != 'little':
        values.byteswap()
    return hashlib.sha256(values.tobytes()).hexdigest()


def baseline_metadata(matrix, ids, document_hashes, execution_sha256):
    """Bind an independently verified baseline matrix; creates no historical proof."""
    rows = read_matrix(matrix['path'], matrix['sha256'])
    require(len(rows) == len(ids) == len(document_hashes) and len(set(ids)) == len(ids), 'baseline alignment')
    return {'schema': 'gamma.recognition-baseline-rows.v1', 'matrix_sha256': matrix['sha256'],
        'execution_sha256': execution_sha256, 'rows': [
            {'problem_id': pid, 'position': i, 'document_sha256': document_hashes[i],
             'vector_sha256': vector_hash(rows[i])} for i, pid in enumerate(ids)]}


def validate_plan(plan):
    require(isinstance(plan, dict) and set(plan) == {'schema', 'release_id', 'execution',
        'baseline', 'population', 'changed_documents', 'boundary_gate', 'encoder', 'code', 'resources'},
        'exact candidate plan fields')
    require(plan['schema'] == SCHEMA and isinstance(plan['release_id'], str) and
            re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._-]{0,127}', plan['release_id']), 'candidate identity')
    fingerprint = execution_identity(plan['execution'])
    require(plan['execution']['dimension'] == DIMENSION, 'existing encoder dimension must remain stable')
    e = plan['execution']
    require(e['device'] == 'cpu' and e['dtype'] == 'float32' and e['threads'] in (1, 2) and
            e['interop_threads'] == 1 and 1 <= e['batch_size'] <= 4 and e['padding_side'] == 'left' and
            e['pooling'] == 'last-token' and e['normalization'] ==
            'L2; torch.nn.functional.normalize(hidden[:, -1].float(), dim=-1)' and
            e['max_tokens'] == 1024 and e['truncation'] ==
            'enabled; right (pinned transformers default); max_length=1024' and e['document_instruction'] == '' and
            e['query_instruction'] == 'Instruct: Given a programming problem, retrieve the identical problem\nQuery: ',
            'execution semantics differ from unchanged pinned CPU adapter')
    require(set(plan['baseline']) == {'id', 'matrix', 'rows'} and isinstance(plan['baseline']['id'], str), 'named original baseline')
    population = plan['population']
    require(isinstance(population, list) and 0 < len(population) <= 10000, 'bounded complete population')
    ids = []
    for row in population:
        require(set(row) == {'problem_id', 'document_sha256', 'action'}, 'exact population metadata')
        require(isinstance(row['problem_id'], str) and boundary_policy._ID.fullmatch(row['problem_id']), 'canonical identity')
        require(isinstance(row['document_sha256'], str) and boundary_policy._HASH.fullmatch(row['document_sha256']), 'document hash')
        require(row['action'] in ('reuse', 'embed'), 'unresolved vector action blocks complete candidate')
        ids.append(row['problem_id'])
    require(len(ids) == len(set(ids)), 'duplicate candidate identity')
    require(set(plan['encoder']) == {'python', 'model_root', 'encoder_manifest', 'cpu_manifest'}, 'encoder descriptors')
    require(plan['encoder']['encoder_manifest']['sha256'] == plan['execution']['model_manifest_sha256'] ==
            plan['execution']['tokenizer_manifest_sha256'], 'existing combined model/tokenizer manifest required')
    require(plan['encoder']['cpu_manifest']['sha256'] == plan['execution']['runtime_manifest_sha256'], 'runtime manifest binding')
    require(set(plan['code']) == set(CODE_FILES), 'complete runner dependency code pins')
    r = plan['resources']
    require(set(r) == {'wall_seconds', 'cpu_seconds', 'cpu_hard_seconds', 'address_space_bytes',
        'aggregate_rss_bytes', 'rss_sample_seconds', 'minimum_available_bytes',
        'require_hard_aggregate_memory'}, 'exact resource envelope')
    for key in ('wall_seconds', 'cpu_seconds', 'cpu_hard_seconds', 'address_space_bytes',
                'aggregate_rss_bytes', 'rss_sample_seconds', 'minimum_available_bytes'):
        require(type(r[key]) in (int, float) and math.isfinite(r[key]) and r[key] > 0, 'positive resource limit')
    require(all(type(r[k]) is int for k in ('cpu_seconds', 'cpu_hard_seconds', 'address_space_bytes',
            'aggregate_rss_bytes', 'minimum_available_bytes')), 'integer resource limits required')
    require(r['cpu_hard_seconds'] >= r['cpu_seconds'] and 0.005 <= r['rss_sample_seconds'] <= .1,
            'CPU/sample resource policy')
    require(r['minimum_available_bytes'] >= 5 * GIB, 'at least 5 GiB headroom required')
    require(type(r['require_hard_aggregate_memory']) is bool, 'explicit hard aggregate requirement')
    return fingerprint


def check_code(plan):
    base = Path(__file__).resolve().parent
    for name, spec in plan['code'].items():
        require(Path(spec['path']) == base / name and sha(regular_path(spec['path'])) == spec['sha256'],
                'runner/dependency code changed: ' + name)
    require(plan['code']['cpu_encoder.py']['sha256'] == plan['execution']['adapter_sha256'], 'adapter/execution binding')


def revalidate_boundary(plan, identities=()):
    gate = pinned(plan['boundary_gate'])
    require(set(gate) == {'schema', 'artifact_paths', 'trusted_hashes'} and
            gate['schema'] == 'gamma.boundary-gate-config.v1', 'boundary gate descriptor')
    boundary = boundary_policy.validate_policy(
        {k: regular_path(p).read_bytes() for k, p in gate['artifact_paths'].items()}, gate['trusted_hashes'])
    for pid in identities:
        boundary.authorize(pid, language='javascript', payload_kind='statement')
    return gate, boundary


def gated_inputs(plan):
    """Authorize the exact changed identities BEFORE opening statement bytes."""
    fingerprint = validate_plan(plan)
    check_code(plan)
    gate, boundary = revalidate_boundary(plan)
    ids = {r['problem_id'] for r in plan['population']}
    require(ids == boundary.authorized | boundary.protected | boundary.unknown, 'complete pinned competitor universe')
    changed = [r for r in plan['population'] if r['action'] == 'embed']
    for row in changed:
        boundary_policy.authorize_before_open(row['problem_id'], gate['artifact_paths'],
            gate['trusted_hashes'], language='javascript', payload_kind='statement')
    documents = pinned(plan['changed_documents'])
    require(set(documents) == {'schema', 'documents'} and
            documents['schema'] == 'gamma.recognition-changed-documents.v1', 'changed document schema')
    require(isinstance(documents['documents'], list) and len(documents['documents']) == len(changed), 'exact changed document count')
    for expected, doc in zip(changed, documents['documents']):
        require(set(doc) == {'problem_id', 'text', 'document_sha256'} and
                doc['problem_id'] == expected['problem_id'] and isinstance(doc['text'], str) and
                0 < len(doc['text']) <= 16384 and doc['text'].strip() and
                hashlib.sha256(doc['text'].encode()).hexdigest() == doc['document_sha256'] == expected['document_sha256'],
                'changed document identity/text binding')
    baseline = pinned(plan['baseline']['rows'])
    require(set(baseline) == {'schema', 'matrix_sha256', 'execution_sha256', 'rows'} and
            baseline['schema'] == 'gamma.recognition-baseline-rows.v1' and
            baseline['matrix_sha256'] == plan['baseline']['matrix']['sha256'] and
            baseline['execution_sha256'] == fingerprint, 'original baseline execution/matrix provenance')
    vectors = read_matrix(plan['baseline']['matrix']['path'], plan['baseline']['matrix']['sha256'])
    require(len(vectors) == len(baseline['rows']), 'baseline row coverage')
    by_id = {}
    for i, row in enumerate(baseline['rows']):
        require(set(row) == {'problem_id', 'position', 'document_sha256', 'vector_sha256'} and
                row['problem_id'] not in by_id and type(row['position']) is int and row['position'] == i and
                row['vector_sha256'] == vector_hash(vectors[i]), 'baseline vector row binding')
        by_id[row['problem_id']] = row
    for row in plan['population']:
        if row['action'] == 'reuse':
            prior = by_id.get(row['problem_id'])
            require(prior is not None and prior['document_sha256'] == row['document_sha256'], 'unproven document reuse')
    pinned(plan['encoder']['encoder_manifest'])
    pinned(plan['encoder']['cpu_manifest'])
    return fingerprint, documents['documents'], vectors, by_id


def default_encoder(plan):
    from .cpu_encoder import PinnedCPUEncoder  # The sole real-model constructor, lazy.
    e, identity = plan['encoder'], plan['execution']
    return PinnedCPUEncoder(e['model_root'], encoder_manifest=e['encoder_manifest']['path'],
        encoder_manifest_sha256=e['encoder_manifest']['sha256'], cpu_manifest=e['cpu_manifest']['path'],
        cpu_manifest_sha256=e['cpu_manifest']['sha256'], native_python_sha256=identity['python_sha256'],
        threads=identity['threads'], batch_size=identity['batch_size'])


def publish_batch(cache, start, raw, receipt):
    """Publish both files in one directory rename; retain incomplete staging evidence."""
    target = cache / f'batch-{start:06d}'
    require(not target.exists(), 'batch already published')
    staging = Path(tempfile.mkdtemp(prefix=f'.batch-{start:06d}-', dir=cache))
    # On any interruption these unpublished bytes remain explicitly separate.
    # A later resume ignores staging and can safely regenerate this batch.
    atomic_bytes(staging / 'vectors.npy', raw)
    atomic_json(staging / 'receipt.json', receipt)
    os.rename(staging, target)
    directory = os.open(cache, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def build_candidate(plan, output, *, encoder_factory=default_encoder):
    """Resume atomic verified batches; retain/ignore interrupted unpublished staging."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    require(output.is_absolute() and not any(p.is_symlink() for p in (output, *output.parents)), 'safe absolute output')
    with os.fdopen(os.open(output / 'worker.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600), 'a+b') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        execution, changed, baseline, by_id = gated_inputs(plan)
        plan_hash = digest(plan)
        identity = {'plan_sha256': plan_hash, 'execution_sha256': execution, 'release_id': plan['release_id']}
        marker = output / 'identity.json'
        if marker.exists():
            require(decode(regular_path(marker).read_bytes()) == identity, 'resume plan/execution drift')
        else:
            atomic_json(marker, identity)
        cache = output / 'batches'
        cache.mkdir(exist_ok=True)
        require(not cache.is_symlink(), 'cache directory symlink')
        generated = {}
        fresh = resumed = 0
        encoder = None
        batch_size = plan['execution']['batch_size']
        for start in range(0, len(changed), batch_size):
            batch = changed[start:start + batch_size]
            revalidate_boundary(plan, [row['problem_id'] for row in batch])
            binding = {'plan_sha256': plan_hash, 'execution_sha256': execution,
                'start': start, 'rows': [{'problem_id': r['problem_id'], 'document_sha256': r['document_sha256']} for r in batch]}
            batch_dir = cache / f'batch-{start:06d}'
            vector_path, receipt_path = batch_dir / 'vectors.npy', batch_dir / 'receipt.json'
            if batch_dir.exists():
                require(batch_dir.is_dir() and not batch_dir.is_symlink() and
                        {p.name for p in batch_dir.iterdir()} == {'vectors.npy', 'receipt.json'},
                        'corrupt published batch retained; do not silently recompute')
                receipt = decode(regular_path(receipt_path).read_bytes())
                require(set(receipt) == {'schema', 'binding', 'binding_sha256', 'vector_sha256', 'request'} and
                        receipt['schema'] == 'gamma.recognition-candidate-batch.v1' and receipt['binding'] == binding and
                        receipt['binding_sha256'] == digest(binding), 'stale batch binding')
                vectors = read_matrix(vector_path, receipt['vector_sha256'])
                resumed += len(batch)
            else:
                if encoder is None:
                    encoder = encoder_factory(plan)
                value = encoder.encode([r['text'] for r in batch], query=False)
                vectors = value.tolist() if hasattr(value, 'tolist') else value
                raw = matrix_bytes(vectors)
                receipt = {'schema': 'gamma.recognition-candidate-batch.v1', 'binding': binding,
                    'binding_sha256': digest(binding), 'vector_sha256': hashlib.sha256(raw).hexdigest(),
                    'request': encoder.last_request_info}
                fresh += len(batch)
            info = receipt['request']
            require(isinstance(info, dict) and info.get('query') is False and info.get('rows') == len(batch) and
                    len(info.get('truncated', [])) == len(batch) and all(v is False for v in info['truncated']), 'missing/truncated document metadata')
            require(len(vectors) == len(batch), 'batch row count')
            if not batch_dir.exists():
                publish_batch(cache, start, raw, receipt)
            for doc, vector in zip(batch, vectors):
                generated[doc['problem_id']] = vector
            atomic_json(output / 'progress.json', {'phase': 'embedding', 'completed': len(generated),
                'total': len(changed), 'release_id': plan['release_id']})
        revalidate_boundary(plan)
        check_code(plan)
        final = [baseline[by_id[r['problem_id']]['position']] if r['action'] == 'reuse' else generated[r['problem_id']]
                 for r in plan['population']]
        raw = matrix_bytes(final)
        matrix_path = output / 'vectors.npy'
        vector_sha = hashlib.sha256(raw).hexdigest()
        if matrix_path.exists():
            require(sha(matrix_path) == vector_sha, 'completed matrix drift')
        else:
            atomic_bytes(matrix_path, raw)
        check_code(plan)
        order = [{'problem_id': r['problem_id'], 'document_sha256': r['document_sha256'],
                  'position': i, 'vector_sha256': vector_hash(final[i])} for i, r in enumerate(plan['population'])]
        summary = {'schema': 'gamma.recognition-candidate-result.v1', **identity,
            'baseline_id': plan['baseline']['id'], 'population': len(final), 'dimension': DIMENSION,
            'reused_vectors': len(final) - len(changed), 'generated_vectors_total': len(changed),
            'generated_vectors_this_attempt': fresh, 'resumed_vectors': resumed,
            'retained_unpublished_staging_directories': sum(p.name.startswith('.batch-') for p in cache.iterdir()),
            'vectors': {'path': str(matrix_path), 'sha256': vector_sha}, 'ordered_rows': order,
            'ordered_rows_sha256': digest(order), 'status': 'candidate_complete_not_qualified',
            'source_availability_filter': False, 'confirmation_read': False, 'activation': False,
            'recognition_qualified': False, 'publication_authorized': False}
        atomic_json(output / 'candidate.json', summary)
        return summary


def memory_cgroup_paths(membership, mounts):
    """Resolve this process, including a cgroup filesystem mounted below root."""
    groups = [line[3:] for line in membership.splitlines() if line.startswith('0::')]
    if not groups:
        return []  # cgroup v1 has no verified aggregate-cap route here.
    require(len(groups) == 1, 'ambiguous unified cgroup membership')
    group = Path(groups[0])
    require(group.is_absolute() and '..' not in group.parts, 'invalid cgroup membership')
    candidates = []
    unescape = lambda text: re.sub(r'\\([0-7]{3})', lambda m: chr(int(m[1], 8)), text)
    for line in mounts.splitlines():
        before, separator, after = line.partition(' - ')
        if not separator or after.split()[0] != 'cgroup2':
            continue
        fields = before.split()
        require(len(fields) >= 6, 'invalid cgroup mount metadata')
        root, point = (Path(unescape(fields[i])) for i in (3, 4))
        require(root.is_absolute() and point.is_absolute() and
                '..' not in root.parts and '..' not in point.parts, 'invalid cgroup mount path')
        if group.is_relative_to(root):
            candidates.append((root, point))
    if not candidates:
        return []
    # Prefer the broadest visible ancestry, so parent limits are not omitted.
    root, point = min(candidates, key=lambda pair: (len(pair[0].parts), str(pair[1])))
    current = point / group.relative_to(root)
    result = [current]
    while current != point:
        current = current.parent
        result.append(current)
    return result


def cgroup_memory_limits():
    paths = memory_cgroup_paths(Path('/proc/self/cgroup').read_text(),
                                Path('/proc/self/mountinfo').read_text())
    limits = []
    for path in paths:
        maximum, current = path / 'memory.max', path / 'memory.current'
        if not maximum.exists() and not current.exists():
            continue  # A controller-disabled child or the unrestricted root.
        require(maximum.exists() and current.exists(), 'incomplete cgroup memory controller')
        value, used = maximum.read_text().strip(), current.read_text().strip()
        require(used.isdecimal() and (value == 'max' or value.isdecimal()), 'invalid cgroup memory accounting')
        if value != 'max':
            limits.append({'path': str(path), 'maximum_bytes': int(value), 'current_bytes': int(used)})
    return limits


def require_memory_cap(resources):
    if not resources.get('require_hard_aggregate_memory', False):
        return []
    limits = cgroup_memory_limits()
    if not any(row['maximum_bytes'] <= resources['aggregate_rss_bytes'] for row in limits):
        raise HardAggregateMemoryUnavailable('no inherited cgroup-v2 cap within the requested memory budget; worker not launched')
    return limits


def available_memory_bytes():
    available = int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines()
                         if line.startswith('MemAvailable:'))) * 1024
    for row in cgroup_memory_limits():
        available = min(available, max(0, row['maximum_bytes'] - row['current_bytes']))
    return available


def preflight(plan):
    validate_plan(plan)
    check_code(plan)
    require_memory_cap(plan['resources'])
    available = available_memory_bytes()
    require(available >= plan['resources']['minimum_available_bytes'], 'less than required effective 5 GiB memory headroom; worker not launched')
    require(sha(Path(plan['encoder']['python']).resolve()) == plan['execution']['python_sha256'], 'runtime Python identity')
    return available


def group_snapshot(pgid):
    """Read only /proc process metadata; do not inspect command lines/environments."""
    found = []
    for path in Path('/proc').iterdir():
        if not path.name.isdigit():
            continue
        try:
            raw = (path / 'stat').read_text()
            fields = raw[raw.rfind(')') + 2:].split()
            if int(fields[2]) != pgid:
                continue
            found.append({'pid': int(path.name), 'start_ticks': int(fields[19]), 'state': fields[0],
                          'rss_bytes': int(fields[21]) * os.sysconf('SC_PAGE_SIZE')})
        except FileNotFoundError:
            continue
        except ProcessLookupError:
            continue
    return found


def cleanup_group(pgid, process):
    try:
        os.killpg(pgid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    deadline = time.monotonic() + 2
    while True:
        process.poll()
        live = [r for r in group_snapshot(pgid) if r['state'] not in ('Z', 'X')]
        if not live:
            return {'verified_no_live_owned_group_members': True, 'remaining_live': []}
        if time.monotonic() >= deadline:
            return {'verified_no_live_owned_group_members': False, 'remaining_live': live}
        try:
            os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        time.sleep(.01)


def supervise(command, output, limits, *, env=None, cwd=None):
    """No graceful leak window: SIGKILL the owned group on EVERY exit path."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    process = None
    peak = 0
    reason = 'worker_error'
    cleanup = {'verified_no_live_owned_group_members': True, 'remaining_live': []}
    caught = None
    kernel_limits = []
    def stop(signum, _frame):
        raise InterruptedError('supervisor signal ' + str(signum))
    previous = {s: signal.getsignal(s) for s in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP)}
    for s in previous:
        signal.signal(s, stop)
    try:
        kernel_limits = require_memory_cap(limits)
        with (output / 'worker.stdout.log').open('ab') as stdout, (output / 'worker.stderr.log').open('ab') as stderr:
            # Block handled signals only across launch/assignment, closing the orphan-launch race.
            mask = signal.pthread_sigmask(signal.SIG_BLOCK, set(previous))
            try:
                process = subprocess.Popen(command, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                    stdout=stdout, stderr=stderr, start_new_session=True)
            finally:
                signal.pthread_sigmask(signal.SIG_SETMASK, mask)
            while True:
                if limits.get('require_hard_aggregate_memory', False):
                    kernel_limits = []
                    kernel_limits = require_memory_cap(limits)
                snapshot = group_snapshot(process.pid)
                rss = sum(r['rss_bytes'] for r in snapshot if r['state'] not in ('Z', 'X'))
                peak = max(peak, rss)
                if rss > limits['aggregate_rss_bytes']:
                    reason = 'sampled_aggregate_rss_limit'
                    break
                if time.monotonic() - started >= limits['wall_seconds']:
                    reason = 'wall_deadline'
                    break
                code = process.poll()
                if code is not None:
                    reason = 'completed' if code == 0 else 'worker_error'
                    break
                time.sleep(min(limits['rss_sample_seconds'], max(0, limits['wall_seconds'] - (time.monotonic() - started))))
    except BaseException as error:
        reason = 'interrupted_or_inspection_error'
        caught = error
    finally:
        # Repeated interrupt signals cannot bypass owned-group cleanup.
        for s in previous:
            signal.signal(s, signal.SIG_IGN)
        if process is not None:
            try:
                cleanup = cleanup_group(process.pid, process)
            except BaseException as error:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                cleanup = {'verified_no_live_owned_group_members': False, 'remaining_live': 'inspection_uncertain',
                           'error_type': type(error).__name__}
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                cleanup['verified_no_live_owned_group_members'] = False
        for s, handler in previous.items():
            signal.signal(s, handler)
        terminal = {'schema': 'gamma.recognition-candidate-supervision.v1', 'reason': reason,
            'worker_pid': process.pid if process else None, 'worker_returncode': process.returncode if process else None,
            'elapsed_seconds': time.monotonic() - started, 'peak_sampled_group_rss_bytes': peak,
            'rss_sample_seconds': limits['rss_sample_seconds'],
            'aggregate_memory_kernel_hard_cap': bool(kernel_limits),
            'inherited_cgroup_limits_last_observed': kernel_limits,
            'wall_limit_seconds': limits['wall_seconds'], 'cleanup': cleanup,
            'status': 'completed' if reason == 'completed' and cleanup['verified_no_live_owned_group_members'] else 'blocked_or_failed',
            'scope': 'cleanup covers the owned process group; an inherited cgroup cap bounds memory, not escaped-process cleanup',
            'source_or_query_payloads_in_terminal': False}
        atomic_json(output / ('supervisor-' + str(time.time_ns()) + '.json'), terminal)
    if caught is not None:
        raise caught
    return terminal


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True)
    parser.add_argument('--plan-sha256', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    output = Path(args.output)
    plan = pinned({'path': args.plan, 'sha256': args.plan_sha256})
    validate_plan(plan)
    if args.worker:
        require(os.getpgrp() == os.getpid(), 'worker requires dedicated owned process group')
        r = plan['resources']
        resource.setrlimit(resource.RLIMIT_AS, (int(r['address_space_bytes']),) * 2)
        resource.setrlimit(resource.RLIMIT_CPU, (int(r['cpu_seconds']), int(r['cpu_hard_seconds'])))
        try:
            preflight(plan)
            result = build_candidate(plan, output)
        except Exception as error:
            output.mkdir(parents=True, exist_ok=True)
            atomic_json(output / 'worker-terminal.json', {'schema': 'gamma.recognition-candidate-worker-terminal.v1',
                'status': 'blocked_or_failed', 'error_type': type(error).__name__,
                'plan_sha256': args.plan_sha256, 'source_or_query_payloads_in_terminal': False})
            raise
        atomic_json(output / 'worker-terminal.json', {'schema': 'gamma.recognition-candidate-worker-terminal.v1',
            'status': 'candidate_complete_not_qualified', 'plan_sha256': args.plan_sha256,
            'candidate_manifest_sha256': sha(output / 'candidate.json'),
            'generated_vectors_this_attempt': result['generated_vectors_this_attempt'],
            'source_or_query_payloads_in_terminal': False})
        return 0
    output.mkdir(parents=True, exist_ok=True)
    try:
        available = preflight(plan)
    except Exception as error:
        atomic_json(output / ('preflight-' + str(time.time_ns()) + '.json'),
            {'schema': 'gamma.recognition-candidate-preflight.v1', 'status': 'blocked',
             'reason': str(error), 'error_type': type(error).__name__, 'worker_launched': False,
             'model_loaded': False, 'new_vectors': 0, 'plan_sha256': args.plan_sha256})
        return 2
    env = {k: v for k, v in os.environ.items() if k in ('PATH', 'LANG', 'LC_ALL')}
    env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1', HF_HUB_OFFLINE='1',
        TRANSFORMERS_OFFLINE='1', OPENBLAS_NUM_THREADS='2', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', CUDA_VISIBLE_DEVICES='')
    repo = Path(__file__).resolve().parents[3]
    command = [plan['encoder']['python'], '-m', 'projects.algorithm_solver.catalogue.recognition_candidate',
        '--worker', '--plan', args.plan, '--plan-sha256', args.plan_sha256, '--output', str(output)]
    terminal = supervise(command, output, plan['resources'], env=env, cwd=repo)
    return 0 if terminal['status'] == 'completed' else 2


if __name__ == '__main__':
    raise SystemExit(main())
