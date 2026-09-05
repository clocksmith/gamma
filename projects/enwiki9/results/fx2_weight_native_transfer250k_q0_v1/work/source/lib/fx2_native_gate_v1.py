"""Bounded native FX2 discovery operations with exact retained inputs."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import time

class GateFailure(ValueError):
    def __init__(self, category, message):
        super().__init__(message)
        self.category = category


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


class NativeGate:
    def __init__(self, root, candidate, caps, validate_only=False):
        self.root, self.candidate, self.caps = root, candidate, caps
        self.result = root / 'results' / candidate
        self.work = self.result / 'work'
        self.started = time.monotonic()
        contract_path = 'operations/adaptive/experiments/' + candidate + '.json'
        content = (root / contract_path).read_bytes()
        self.reference = {'path': contract_path, 'sha256': 'sha256:' + hashlib.sha256(content).hexdigest()}
        if not validate_only:
            require(self.reference == json.loads(os.environ['GAMMA_ENWIKI9_EXPERIMENT_JSON']), 'experiment binding changed')
        self.contract = json.loads(content)
        require(self.contract['experimentId'] == candidate and self.contract['status'] == 'frozen', 'wrong experiment')
        self.inputs = {row['path']: row for row in self.contract['inputs']}
        require(len(self.inputs) == len(self.contract['inputs']), 'duplicate input paths')
        self.buffers = {}
        for name, ref in self.inputs.items():
            path = root / name
            require(not Path(name).is_absolute() and '..' not in Path(name).parts and path.resolve() == path, 'aliased input: ' + name)
            with path.open('rb') as handle:
                before = os.fstat(handle.fileno())
                data = handle.read()
                after = os.fstat(handle.fileno())
            identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
            require(identity(before) == identity(after) == identity(path.stat()), 'input replaced while read: ' + name)
            require(hashlib.sha256(data).hexdigest() == ref['sha256'].removeprefix('sha256:'), 'input changed: ' + name)
            self.buffers[name] = data
        self.toolchain = json.loads(self.buffers['operations/provenance/public_fx2_gcc15_toolchain_20260905.json'])
        self.verify()
        self.helpers = {}
        exec(compile(self.buffers['lib/artifacts.py'], str(root / 'lib/artifacts.py'), 'exec'), self.helpers)
        self.commands, self.binaries, self.retained = [], {}, {}
        if validate_only:
            return
        require(os.sched_getaffinity(0) == {2}, 'canonical parent must already use CPU2')
        self.marker = Path(os.environ['GAMMA_RESOURCE_PHASE_MARKERS'])
        job_id = self.marker.parent.name.removesuffix('.resources')
        require(self.marker == root / 'run_logs/adaptive' / (job_id + '.resources/phases.jsonl') and self.marker.resolve() == self.marker, 'wrong phase owner')
        jobs = list((root / 'operations/adaptive/running').glob('*' + job_id + '.json'))
        require(len(jobs) == 1, 'missing or ambiguous running job')
        job = read(jobs[0])
        require(job['job_id'] == job_id and job['candidate_id'] == candidate and job['state'] == 'running' and job['experiment'] == self.reference and job['execution_mode'] == 'discovery', 'running job identity differs')
        require(all(job['resource_budget'].get(k) == v for k, v in caps.items()), 'running budget differs')
        self.group = Path(job['execution_resources']['cgroup_path'])
        membership = next(line[3:] for line in Path('/proc/self/cgroup').read_text().splitlines() if line.startswith('0::'))
        require(self.group == Path('/sys/fs/cgroup' + membership) and self.group.stat().st_ino == job['execution_resources']['cgroup_inode'], 'wrong resource group')
        require((self.group / 'memory.max').read_text().strip() == str(caps['memory_bytes']) and (self.group / 'memory.swap.max').read_text().strip() == '0', 'wrong memory limits')
        require(self.result.is_dir() and self.result.resolve() == self.result and not any(self.result.iterdir()), 'result directory must be empty')
        (self.work / 'tmp').mkdir(parents=True)
        # Import project dependencies only through a fresh owned bytecode path.
        # The canonical contract also binds their complete source closure.
        import sys
        sys.pycache_prefix = str(self.work / 'tmp/pycache')
        self.env = {'PATH': '/usr/bin:/bin', 'LC_ALL': 'C', 'TMPDIR': str(self.work / 'tmp'), 'PYTHONDONTWRITEBYTECODE': '1'}
        os.environ['TMPDIR'] = self.env['TMPDIR']

    def verify(self):
        for name, ref in self.inputs.items():
            require(sha(self.root / name) == ref['sha256'].removeprefix('sha256:'), 'frozen input changed: ' + name)
        for row in self.toolchain['toolchain']:
            require(sha(row['path']) == row['sha256'] and Path(row['path']).stat().st_size == row['bytes'], 'toolchain changed: ' + row['name'])
            alias = Path('/usr/bin') / row['name']
            if alias.exists():
                require(alias.resolve() == Path(row['path']), 'toolchain alias changed: ' + row['name'])
        for path, digest in getattr(self, 'retained', {}).items():
            require(sha(path) == digest, 'retained source changed: ' + str(path))
        for path, digest in getattr(self, 'binaries', {}).items():
            require(sha(path) == digest, 'compiled binary changed: ' + path)

    def artifact(self, path):
        return self.helpers['artifact_ref'](path, self.root)

    def write(self, name, value):
        self.helpers['atomic_write_json'](self.result / name, value)

    def copy(self, source, target):
        require(source in self.buffers, 'unbound materialized input: ' + source)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as handle:
            handle.write(self.buffers[source])
        require(sha(target) == self.inputs[source]['sha256'].removeprefix('sha256:'), 'materialized copy differs: ' + source)

    def retain_sources(self):
        for source in self.buffers:
            if Path(source).suffix in ('.py', '.cpp', '.h', '.hpp') or Path(source).name == 'LICENSE':
                target = self.work / 'source' / source
                self.copy(source, target)
                target.chmod(0o444)
                self.retained[target] = self.inputs[source]['sha256'].removeprefix('sha256:')

    def adapter(self, path, work, source_paths=None):
        adapter = json.loads(self.buffers[path])
        for row in adapter.get('files', [adapter]):
            if source_paths is not None and row['source_path'] not in source_paths:
                continue
            target = work / row['source_path']
            require(sha(target) == row['source_sha256'], 'adapter preimage changed')
            text = target.read_text()
            for replacement in row['replacements']:
                require(text.count(replacement['before']) == 1, 'adapter anchor ambiguous')
                text = text.replace(replacement['before'], replacement['after'])
            target.write_text(text)
            require(sha(target) == row['patched_sha256'], 'adapter postimage changed')

    def closure(self):
        require({int(p) for p in (self.group / 'cgroup.procs').read_text().split()} == {os.getpid()}, 'native children remain')

    def run(self, name, argv, cap, env=None, accepted=(0,), work=None):
        require(name and '/' not in name and all(p['phase'] != name for p in self.commands), 'invalid or duplicate phase')
        require(isinstance(cap, int) and cap > 0, 'phase cap must be a positive integer')
        remaining = int(self.started + self.caps['wall_seconds'] - time.monotonic())
        if remaining <= 0:
            raise GateFailure('budget_exhausted', 'aggregate stop before ' + name)
        cap = min(cap, remaining)
        if argv[0] in self.binaries:
            require(sha(argv[0]) == self.binaries[argv[0]], 'binary changed before phase')
        command = ['/usr/bin/timeout', '--signal=TERM', '--kill-after=2', str(cap), *argv]
        usage = lambda: resource.getrusage(resource.RUSAGE_CHILDREN)
        try:
            before = usage()
        except OSError:
            before = None
        with self.marker.open('a') as f:
            f.write(json.dumps({'phase': name, 'event': 'start'}) + '\n')
        started, code, error = time.monotonic(), None, None
        try:
            with (self.result / (name + '.stdout')).open('xb') as out, (self.result / (name + '.stderr')).open('xb') as err:
                code = subprocess.run(command, cwd=work or self.work, env={**self.env, **(env or {})}, stdout=out, stderr=err).returncode
        except OSError as failure:
            error = str(failure)
        try:
            after = usage()
        except OSError:
            after = None
        row = {'phase': name, 'command': command, 'environment': env or {}, 'returncode': code, 'accepted_returncodes': list(accepted), 'elapsed_seconds': time.monotonic() - started, 'elapsed_cap_seconds': cap, 'user_cpu_seconds': after.ru_utime - before.ru_utime if before and after else None, 'system_cpu_seconds': after.ru_stime - before.ru_stime if before and after else None, 'missing_diagnostics': [] if before and after else ['optional child CPU telemetry unavailable'], 'timing_authority': 'shared-host diagnostic', 'launch_error': error}
        self.write(name + '.execution.json', row)
        self.commands.append(row)
        with self.marker.open('a') as f:
            f.write(json.dumps({'phase': name, 'event': 'end'}) + '\n')
        self.closure()
        if error or code not in accepted:
            raise GateFailure('budget_exhausted' if code == 124 else 'resource_or_signal_stop' if code == 137 else 'execution_failed', name + ' exited ' + str(code))
        if argv[0] in self.binaries:
            require(sha(argv[0]) == self.binaries[argv[0]], 'binary changed after phase')
        return row

    def compare_trace(self, reference, target, expected_bytes):
        require(reference.stat().st_size == expected_bytes and target.stat().st_size == expected_bytes, 'coder record length differs')
        offset, blocks = 0, []
        with reference.open('rb') as left, target.open('rb') as right:
            while a := left.read(28 * 4096):
                b = right.read(len(a))
                if a != b:
                    first = offset + next(i for i, (x, y) in enumerate(zip(a, b)) if x != y)
                    context = max(0, first // 28 - 2) * 28
                    left.seek(context)
                    right.seek(context)
                    self.write('first-divergence.json', {'reference': self.artifact(reference), 'target': self.artifact(target), 'first_byte': first, 'first_bit_record': first // 28, 'context_first_record': context // 28, 'reference_hex': left.read(28 * 5).hex(), 'target_hex': right.read(28 * 5).hex()})
                    raise ValueError('coder records diverge at byte ' + str(first))
                blocks.append({'first_record': offset // 28, 'record_count': len(a) // 28, 'sha256': hashlib.sha256(a).hexdigest()})
                offset += len(a)
        return {'reference': self.artifact(reference), 'target': self.artifact(target), 'exact_byte_comparison': True, 'blocks': blocks}
