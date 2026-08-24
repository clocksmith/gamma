"""Run one inherited SAFE-MIX proof phase behind a receipt-bound barrier.

Revision 1 of the external activation plan is intentionally dormant. This
entry point must reject before creating output until a future revision binds
terminal qm8 evidence, its independent classification, every source/runtime
identity, an available toolchain, and one exact guarded phase command.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import stat
import subprocess
import sys
from typing import Any
PROJECT = Path(__file__).resolve().parents[2]
CANDIDATE_ID = 'gamma_safe_mix_v2'
SUBJECT_ID = 'gamma_safe_mix_v1'
PLAN = PROJECT / 'operations/planning/gamma_safe_mix_v2_execution.json'
PLAN_SCHEMA = PROJECT / 'operations/planning/gamma-safe-mix-v2-execution.schema.json'
LEASE = PROJECT / 'operations/runtime/exclusive_full1g.json'
LOCK = PROJECT / 'operations/runtime/exclusive_full1g.json.lock'
RESULT_ROOT = PROJECT / 'results/gamma_safe_mix_v2'
SCRATCH_ROOT = PROJECT / 'scratch/gamma_safe_mix_v2'
V1_ROOT = PROJECT / 'programs/gamma_safe_mix_v1'
GUARD = PROJECT / 'tools/run_with_resource_guard_v3.py'
GUARD_SCHEMA = PROJECT / 'contracts/research/v1/resource-guard-receipt.v3.schema.json'
OWNED_CLEANUP_MANAGER = PROJECT / 'programs/gamma_managed_exclusive_lease_owned_cleanup_q0_v1/managed_exclusive_lease.py'
CANONICAL_LEASE_MANAGER = PROJECT / 'tools/managed_exclusive_lease.py'
PYTHON = Path('/usr/bin/python3.14')
BASE_ENV = {'LANG': 'C', 'LC_ALL': 'C', 'PATH': '/usr/bin:/bin', 'PYTHONHASHSEED': '0', 'TZ': 'UTC'}
PHASES = {'build_negative_controls': {'entrypoint': 'safe-mix-build-negative-controls.py', 'receipt_schema': 'gamma.enwiki9.safe-mix-build-negative-controls-receipt.v1', 'pass_fields': ('positive_fixture_pass', 'all_controls_rejected_pass'), 'lease': True, 'program_lock': False, 'toolchain': False}, 'build_a': {'entrypoint': 'safe-mix-build-capture.py', 'receipt_schema': 'gamma.enwiki9.safe-mix-build-receipt.v1', 'pass_fields': ('terminal_pass',), 'lease': True, 'program_lock': True, 'toolchain': True}, 'build_b': {'entrypoint': 'safe-mix-build-capture.py', 'receipt_schema': 'gamma.enwiki9.safe-mix-build-receipt.v1', 'pass_fields': ('terminal_pass',), 'lease': True, 'program_lock': True, 'toolchain': True}, 'build_verify': {'entrypoint': 'safe-mix-build-verify.py', 'receipt_schema': 'gamma.enwiki9.safe-mix-independent-build-verification.v1', 'pass_fields': ('terminal_pass',), 'lease': False, 'program_lock': False, 'toolchain': False}, 'transactional_controls': {'entrypoint': 'safe-mix-negative-controls-capture.py', 'receipt_schema': 'gamma.enwiki9.safe-mix-negative-controls-execution-receipt.v1', 'pass_fields': ('terminal_pass',), 'lease': True, 'program_lock': True, 'toolchain': False}, 'oracle_suite': {'entrypoint': 'safe-mix-oracle-suite.py', 'receipt_schema': 'gamma.enwiki9.safe-mix-oracle-suite-receipt.v1', 'pass_fields': ('all_populations_pass',), 'lease': True, 'program_lock': True, 'toolchain': False}}

def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode('utf-8')

def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()

def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()

def regular(path: Path, label: str, executable: bool=False) -> Path:
    metadata = path.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise RuntimeError(f'{label} must be a single-link nonsymlink regular file')
    resolved = path.resolve(strict=True)
    if executable and (not os.access(resolved, os.X_OK)):
        raise RuntimeError(f'{label} is not executable')
    return resolved

def load_object(path: Path, label: str) -> tuple[Path, dict[str, Any]]:
    selected = regular(path, label)
    value = json.loads(selected.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise RuntimeError(f'{label} root is not an object')
    return (selected, value)

def artifact(path: Path) -> dict[str, Any]:
    selected = regular(path, str(path))
    try:
        display = selected.relative_to(PROJECT).as_posix()
    except ValueError:
        display = str(selected)
    return {'path': display, 'bytes': selected.stat().st_size, 'sha256': sha256(selected)}

def resolve_binding(record: Any, label: str) -> Path:
    if not isinstance(record, dict) or set(record) != {'path', 'bytes', 'sha256'}:
        raise RuntimeError(f'{label} binding has the wrong shape')
    declared = Path(record['path'])
    path = declared if declared.is_absolute() else PROJECT / declared
    selected = regular(path, label)
    if selected.stat().st_size != record['bytes'] or sha256(selected) != record['sha256']:
        raise RuntimeError(f'{label} binding differs')
    return selected

def require_absent(path: Path, label: str) -> None:
    try:
        os.lstat(path)
    except FileNotFoundError:
        return
    raise RuntimeError(f'{label} is occupied: {path}')

class OwnedLock:

    def __init__(self, lock_path: Path, directory_descriptor: int, lock_descriptor: int, device: int, inode: int, payload: bytes) -> None:
        self.lock_path = lock_path
        self.directory_descriptor = directory_descriptor
        self.lock_descriptor = lock_descriptor
        self.device = device
        self.inode = inode
        self.payload = payload
        self.closed = False

    @classmethod
    def acquire(cls, lock_path: Path=LOCK) -> 'OwnedLock':
        directory_descriptor = os.open(lock_path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW)
        lock_descriptor = -1
        payload = b''
        try:
            lock_descriptor = os.open(lock_path.name, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW, 384, dir_fd=directory_descriptor)
            payload = canonical({'candidate_id': CANDIDATE_ID, 'pid': os.getpid(), 'token': secrets.token_hex(32)})
            offset = 0
            while offset < len(payload):
                written = os.write(lock_descriptor, payload[offset:])
                if written <= 0:
                    raise OSError('short managed acquisition-lock write')
                offset += written
            os.fsync(lock_descriptor)
            os.fsync(directory_descriptor)
            metadata = os.fstat(lock_descriptor)
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
                raise RuntimeError('new managed acquisition lock has invalid metadata')
            return cls(lock_path, directory_descriptor, lock_descriptor, metadata.st_dev, metadata.st_ino, payload)
        except BaseException:
            if lock_descriptor >= 0:
                try:
                    descriptor = os.fstat(lock_descriptor)
                    current = os.stat(lock_path.name, dir_fd=directory_descriptor, follow_symlinks=False)
                    if payload and stat.S_ISREG(descriptor.st_mode) and stat.S_ISREG(current.st_mode) and (descriptor.st_nlink == 1) and (current.st_nlink == 1) and ((descriptor.st_dev, descriptor.st_ino) == (current.st_dev, current.st_ino)) and (os.pread(lock_descriptor, len(payload) + 1, 0) == payload):
                        os.unlink(lock_path.name, dir_fd=directory_descriptor)
                        os.fsync(directory_descriptor)
                except OSError:
                    pass
                finally:
                    os.close(lock_descriptor)
            os.close(directory_descriptor)
            raise

    def verify(self) -> None:
        if self.closed:
            raise RuntimeError('managed acquisition lock is already closed')
        descriptor = os.fstat(self.lock_descriptor)
        current = os.stat(self.lock_path.name, dir_fd=self.directory_descriptor, follow_symlinks=False)
        if not stat.S_ISREG(descriptor.st_mode) or not stat.S_ISREG(current.st_mode) or descriptor.st_nlink != 1 or (current.st_nlink != 1) or ((descriptor.st_dev, descriptor.st_ino) != (self.device, self.inode)) or ((current.st_dev, current.st_ino) != (self.device, self.inode)) or (os.pread(self.lock_descriptor, len(self.payload) + 1, 0) != self.payload):
            raise RuntimeError('managed acquisition-lock ownership was lost')

    def witness(self) -> dict[str, Any]:
        self.verify()
        return {'device': self.device, 'inode': self.inode, 'payload_bytes': len(self.payload), 'payload_sha256': sha256_bytes(self.payload)}

    def release(self) -> None:
        try:
            self.verify()
            os.unlink(self.lock_path.name, dir_fd=self.directory_descriptor)
            os.fsync(self.directory_descriptor)
        finally:
            self.closed = True
            os.close(self.lock_descriptor)
            os.close(self.directory_descriptor)

def process_identity(pid: int, proc_root: Path=Path('/proc')) -> tuple[int, int] | None:
    try:
        raw = (proc_root / str(pid) / 'stat').read_text(encoding='ascii')
        close = raw.rfind(')')
        fields = raw[close + 2:].split()
        return (int(fields[1]), int(fields[19]))
    except (OSError, IndexError, ValueError):
        return None

def ancestor_pids(proc_root: Path=Path('/proc')) -> set[int]:
    found: set[int] = set()
    cursor = os.getpid()
    while cursor > 1 and cursor not in found:
        found.add(cursor)
        identity = process_identity(cursor, proc_root)
        if identity is None:
            break
        cursor = identity[0]
    return found

def live_qm8_processes(proc_root: Path=Path('/proc')) -> list[dict[str, Any]]:
    excluded = ancestor_pids(proc_root) if proc_root == Path('/proc') else set()
    found: list[dict[str, Any]] = []
    for process in proc_root.iterdir():
        if not process.name.isdigit():
            continue
        pid = int(process.name)
        if pid in excluded:
            continue
        try:
            raw = (process / 'cmdline').read_bytes()
        except OSError:
            continue
        command = raw.replace(b'\x00', b' ').decode('utf-8', errors='replace')
        if any((token in command for token in ('cmix_filebacked_fxcm_full_a_qm8_v1', 'scratch/cmix_filebacked_fxcm_full_a_qm8_v1', 'results/cmix_filebacked_fxcm_full_a_qm8_v1'))):
            identity = process_identity(pid, proc_root)
            found.append({'pid': pid, 'parent_pid': None if identity is None else identity[0], 'start_ticks': None if identity is None else identity[1], 'command': command})
    return sorted(found, key=lambda item: item['pid'])

def require_project_path(path: Path, root: Path, label: str) -> Path:
    candidate = path if path.is_absolute() else PROJECT / path
    normalized = Path(os.path.abspath(candidate))
    expected_root = Path(os.path.abspath(root))
    try:
        normalized.relative_to(expected_root)
    except ValueError as exc:
        raise RuntimeError(f'{label} escapes {expected_root}') from exc
    cursor = normalized.parent
    while cursor != expected_root.parent and cursor != cursor.parent:
        if cursor.exists() or cursor.is_symlink():
            metadata = cursor.lstat()
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
                raise RuntimeError(f'{label} has a non-directory or symlink parent')
        if cursor == expected_root:
            break
        cursor = cursor.parent
    return normalized

def absolute_argument(value: str, label: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        raise RuntimeError(f'{label} must be an absolute path')
    return path

def option_value(command: list[str], option: str, required: bool=True) -> str | None:
    positions = [index for index, item in enumerate(command) if item == option]
    if not positions:
        if required:
            raise RuntimeError(f'command omits {option}')
        return None
    if len(positions) != 1 or positions[0] + 1 >= len(command):
        raise RuntimeError(f'command has an invalid or duplicated {option}')
    return command[positions[0] + 1]

def terminal_evidence(plan: dict[str, Any]) -> tuple[Path, dict[str, Any], Path, dict[str, Any]]:
    activation = plan['activation']
    terminal_path = resolve_binding(activation['qm8_terminal_receipt'], 'qm8 terminal receipt')
    classification_path = resolve_binding(activation['qm8_terminal_classification'], 'qm8 terminal classification')
    terminal = json.loads(terminal_path.read_text(encoding='utf-8'))
    classification = json.loads(classification_path.read_text(encoding='utf-8'))
    if terminal.get('schema') != 'gamma.enwiki9.cmix-filebacked-fxcm-full-roundtrip.v1' or terminal.get('candidate_id') != 'cmix_obias_memory_safe_parent_filebacked_q1_v1' or terminal.get('arm') != 'a' or (not isinstance(terminal.get('terminal_pass'), bool)):
        raise RuntimeError('qm8 terminal receipt has the wrong identity or state')
    expected_schema = 'gamma.enwiki9.cmix-filebacked-fxcm-full-soft-high-verification.v1' if terminal['terminal_pass'] else 'gamma.enwiki9.cmix-filebacked-fxcm-full-qm8-failure-verification.v1'
    if classification.get('schema') != expected_schema or classification.get('verification_pass') is not True or classification.get('gamma_score_credit_bytes') != 0:
        raise RuntimeError('qm8 terminal classification is not a matching pass')
    return (terminal_path, terminal, classification_path, classification)

def managed_lease_evidence(plan: dict[str, Any]) -> tuple[Path, dict[str, Any], Path]:
    activation = plan['activation']
    verification_path = resolve_binding(activation['managed_lease_verification'], 'managed-lease verification')
    canonical_manager = resolve_binding(activation['canonical_lease_manager'], 'canonical managed-lease implementation')
    verification = json.loads(verification_path.read_text(encoding='utf-8'))
    if verification.get('schema') != 'gamma.enwiki9.managed-exclusive-lease-owned-cleanup-verification.v1' or verification.get('candidate_id') != 'gamma_managed_exclusive_lease_owned_cleanup_q0_v1' or verification.get('verified') is not True or (verification.get('canonical_migration_authorized') is not True) or (verification.get('archive_authority') is not False) or (verification.get('gamma_compression_credit_bytes') != 0) or (verification.get('gamma_score_credit_bytes') != 0):
        raise RuntimeError('managed-lease ownership proof is not a promotion pass')
    if canonical_manager != CANONICAL_LEASE_MANAGER.resolve(strict=True):
        raise RuntimeError('activation does not bind the canonical lease manager')
    if sha256(canonical_manager) != sha256(regular(OWNED_CLEANUP_MANAGER, 'owned-cleanup manager')):
        raise RuntimeError('canonical lease manager has not migrated to the proven implementation')
    return (verification_path, verification, canonical_manager)

def toolchain_probes(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    expected_markers = {'compiler': b'clang', 'linker': b'lld'}
    output: dict[str, dict[str, Any]] = {}
    for name, marker in expected_markers.items():
        path = resolve_binding(plan['activation']['toolchain'][name], name)
        if not os.access(path, os.X_OK):
            raise RuntimeError(f'bound {name} is not executable')
        command = [str(path), '--version']
        completed = subprocess.run(command, env=BASE_ENV, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, close_fds=True)
        combined = (completed.stdout + b'\n' + completed.stderr).lower()
        if completed.returncode != 0 or marker not in combined:
            raise RuntimeError(f'bound {name} does not satisfy the frozen tool family')
        output[name] = {'command': command, 'command_sha256': sha256_bytes(canonical(command)), 'return_code': completed.returncode, 'stdout_sha256': sha256_bytes(completed.stdout), 'stderr_sha256': sha256_bytes(completed.stderr), 'family_marker_pass': True}
    return output

def validate_plan() -> tuple[Path, dict[str, Any]]:
    plan_path, plan = load_object(PLAN, 'SAFE-MIX v2 activation plan')
    regular(PLAN_SCHEMA, 'SAFE-MIX v2 activation-plan schema')
    if set(plan) != {'schema', 'candidate_id', 'subject_candidate_id', 'revision', 'operational_status', 'execution_authorized', 'source_bindings', 'activation', 'phases', 'archive_authority', 'gamma_compression_credit_bytes', 'gamma_score_credit_bytes', 'claim_boundary'} or plan.get('schema') != 'gamma.enwiki9.safe-mix-v2-execution-plan.v1' or plan.get('candidate_id') != CANDIDATE_ID or (plan.get('subject_candidate_id') != SUBJECT_ID) or (plan.get('revision', 0) < 2) or (plan.get('operational_status') != 'activated_after_qm8_terminal') or (plan.get('execution_authorized') is not True) or (plan.get('archive_authority') is not False) or (plan.get('gamma_compression_credit_bytes') != 0) or (plan.get('gamma_score_credit_bytes') != 0):
        raise RuntimeError('SAFE-MIX v2 activation plan is dormant or malformed')
    activation = plan.get('activation')
    if not isinstance(activation, dict) or set(activation) != {'qm8_terminal_receipt', 'qm8_terminal_classification', 'managed_lease_verification', 'canonical_lease_manager', 'toolchain'} or (not isinstance(plan.get('claim_boundary'), list)) or (not plan['claim_boundary']) or (not all((isinstance(item, str) and item for item in plan['claim_boundary']))):
        raise RuntimeError('SAFE-MIX v2 activation fields differ')
    expected = {'activation_gate': Path(__file__).resolve(strict=True), 'activation_verifier': V1_ROOT.parent / CANDIDATE_ID / 'activation_verify.py', 'plan_schema': PLAN_SCHEMA, 'activation_receipt_schema': V1_ROOT.parent / CANDIDATE_ID / 'activation-receipt.schema.json', 'activation_verification_schema': V1_ROOT.parent / CANDIDATE_ID / 'activation-verification.schema.json', 'v1_program_lock': V1_ROOT / 'program-lock.json', 'v1_program_lock_verification': PROJECT / 'results/gamma_safe_mix_v1/01_program_lock/program-lock-verification.json', 'activation_audit': PROJECT / 'operations/planning/gamma_safe_mix_v1_activation_audit_q0_v1.json', 'lease_schema': PROJECT / 'operations/runtime/exclusive_full1g.schema.json', 'owned_cleanup_manager': OWNED_CLEANUP_MANAGER, 'resource_guard': GUARD, 'resource_guard_schema': GUARD_SCHEMA, 'python_runtime': PYTHON}
    bindings = plan.get('source_bindings')
    if not isinstance(bindings, dict) or set(bindings) != set(expected):
        raise RuntimeError('activation source-binding set differs')
    for name, path in expected.items():
        selected = resolve_binding(bindings[name], name)
        if selected != path.resolve(strict=True):
            raise RuntimeError(f'activation binding path differs for {name}')
    for name in ('compiler', 'linker'):
        selected = resolve_binding(plan['activation']['toolchain'][name], name)
        if not os.access(selected, os.X_OK):
            raise RuntimeError(f'bound {name} is not executable')
    terminal_evidence(plan)
    managed_lease_evidence(plan)
    return (plan_path, plan)

def validate_phase(plan: dict[str, Any], phase: str) -> tuple[dict[str, Any], list[str], dict[str, Path]]:
    if phase not in PHASES:
        raise RuntimeError(f'unknown SAFE-MIX proof phase: {phase}')
    definition = PHASES[phase]
    phases = plan.get('phases')
    if not isinstance(phases, dict) or set(phases) != set(PHASES):
        raise RuntimeError('activated plan does not bind the complete proof-phase set')
    specification = phases[phase]
    required = {'entrypoint', 'child_receipt_schema', 'child_receipt', 'guard_receipt', 'gate_receipt', 'phase_result_root', 'phase_scratch_root', 'argv'}
    if not isinstance(specification, dict) or set(specification) != required:
        raise RuntimeError('proof-phase specification has the wrong shape')
    expected_entrypoint = V1_ROOT / definition['entrypoint']
    if resolve_binding(specification['entrypoint'], f'{phase} entrypoint') != expected_entrypoint.resolve(strict=True):
        raise RuntimeError('proof-phase entrypoint differs')
    schema_path = resolve_binding(specification['child_receipt_schema'], f'{phase} receipt schema')
    schema = json.loads(schema_path.read_text(encoding='utf-8'))
    if schema.get('$id') != definition['receipt_schema']:
        raise RuntimeError('proof-phase receipt-schema identity differs')
    command = specification['argv']
    if not isinstance(command, list) or not command or (not all((isinstance(item, str) for item in command))):
        raise RuntimeError('proof-phase argv is invalid')
    separator = [index for index, item in enumerate(command) if item == '--']
    if len(separator) != 1:
        raise RuntimeError('guarded command must contain exactly one separator')
    split = separator[0]
    outer, child = (command[:split], command[split + 1:])
    if len(outer) < 2 or len(child) < 2:
        raise RuntimeError('guarded command is incomplete')
    if absolute_argument(outer[0], 'guard Python').resolve(strict=True) != PYTHON.resolve(strict=True) or absolute_argument(outer[1], 'resource guard').resolve(strict=True) != GUARD.resolve(strict=True):
        raise RuntimeError('proof phase does not use the bound Python and resource guard')
    if absolute_argument(child[0], 'child Python').resolve(strict=True) != PYTHON.resolve(strict=True) or absolute_argument(child[1], 'child entrypoint').resolve(strict=True) != expected_entrypoint.resolve(strict=True):
        raise RuntimeError('proof phase does not use the bound inherited entrypoint')
    child_receipt = require_project_path(Path(specification['child_receipt']), RESULT_ROOT, 'child receipt')
    guard_receipt = require_project_path(Path(specification['guard_receipt']), RESULT_ROOT, 'guard receipt')
    gate_receipt = require_project_path(Path(specification['gate_receipt']), RESULT_ROOT, 'gate receipt')
    result_root = require_project_path(Path(specification['phase_result_root']), RESULT_ROOT, 'phase result root')
    scratch_root = require_project_path(Path(specification['phase_scratch_root']), SCRATCH_ROOT, 'phase scratch root')
    if result_root != RESULT_ROOT / phase or scratch_root != SCRATCH_ROOT / phase or len({child_receipt, guard_receipt, gate_receipt}) != 3:
        raise RuntimeError('proof-phase output topology differs')
    for receipt in (child_receipt, guard_receipt, gate_receipt):
        if receipt == result_root or not receipt.is_relative_to(result_root):
            raise RuntimeError('proof receipt escapes its phase result root')
    if absolute_argument(option_value(outer, '--guard-json'), 'guard receipt argv') != guard_receipt:
        raise RuntimeError('guard receipt argv differs from phase declaration')
    if absolute_argument(option_value(child, '--receipt'), 'child receipt argv') != child_receipt:
        raise RuntimeError('child receipt argv differs from phase declaration')
    scratch_arguments = [outer[index + 1] for index, item in enumerate(outer[:-1]) if item == '--scratch-path']
    if str(result_root) not in scratch_arguments or str(scratch_root) not in scratch_arguments:
        raise RuntimeError('guard command does not bind both result and scratch roots')
    if definition['lease']:
        if absolute_argument(option_value(child, '--exclusive-lease'), 'exclusive lease argv') != LEASE:
            raise RuntimeError('child command does not bind the canonical lease')
    elif option_value(child, '--exclusive-lease', required=False) is not None:
        raise RuntimeError('phase unexpectedly accepts an exclusive lease argument')
    if definition['program_lock']:
        if absolute_argument(option_value(child, '--program-lock'), 'program lock argv').resolve(strict=True) != (V1_ROOT / 'program-lock.json').resolve(strict=True):
            raise RuntimeError('child command does not bind the v1 program lock')
    if definition['toolchain']:
        toolchain = plan['activation']['toolchain']
        compiler = resolve_binding(toolchain['compiler'], 'compiler')
        linker = resolve_binding(toolchain['linker'], 'linker')
        if absolute_argument(option_value(child, '--compiler'), 'compiler argv').resolve(strict=True) != compiler:
            raise RuntimeError('child compiler differs from activation')
        if absolute_argument(option_value(child, '--linker'), 'linker argv').resolve(strict=True) != linker:
            raise RuntimeError('child linker differs from activation')
    for output in (child_receipt, guard_receipt, gate_receipt, result_root, scratch_root):
        require_absent(output, 'proof output')
    paths = {'child_receipt': child_receipt, 'guard_receipt': guard_receipt, 'gate_receipt': gate_receipt, 'result_root': result_root, 'scratch_root': scratch_root}
    return (specification, command, paths)

def child_pass(value: dict[str, Any], phase: str) -> bool:
    definition = PHASES[phase]
    return bool(value.get('schema') == definition['receipt_schema'] and value.get('candidate_id') == SUBJECT_ID and all((value.get(field) is True for field in definition['pass_fields'])) and (value.get('execution_authority') is False) and (value.get('archive_authority') is False) and (value.get('score_credit_bytes') == 0))

def guard_pass(value: dict[str, Any]) -> bool:
    guards = value.get('guards')
    return bool(value.get('schema') == 'gamma.enwiki9.resource-guard-receipt.v3' and value.get('status') == 'complete' and (value.get('returncode') == 0) and isinstance(guards, dict) and guards and (not any(guards.values())))

def write_new(path: Path, value: dict[str, Any]) -> None:
    raw = canonical(value)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW, 384)
    try:
        offset = 0
        while offset < len(raw):
            written = os.write(descriptor, raw[offset:])
            if written <= 0:
                raise OSError('short activation-receipt write')
            offset += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=sorted(PHASES), required=True)
    args = parser.parse_args()
    plan_path, plan = validate_plan()
    terminal_path, _, classification_path, _ = terminal_evidence(plan)
    lease_verification_path, _, canonical_manager = managed_lease_evidence(plan)
    probes = toolchain_probes(plan)
    require_absent(LEASE, 'canonical managed lease')
    require_absent(LOCK, 'canonical managed acquisition lock')
    live_before = live_qm8_processes()
    if live_before:
        raise RuntimeError(f'qm8 processes remain live: {live_before}')
    specification, command, paths = validate_phase(plan, args.phase)
    owned_lock = OwnedLock.acquire()
    lock_witness = owned_lock.witness()
    try:
        require_absent(LEASE, 'post-acquire canonical managed lease')
        live_after_acquire = live_qm8_processes()
        if live_after_acquire:
            raise RuntimeError(f'qm8 process appeared after lock acquisition: {live_after_acquire}')
        result_root = paths['result_root']
        scratch_root = paths['scratch_root']
        result_root.mkdir(mode=448, parents=True)
        scratch_root.mkdir(mode=448, parents=True)
        completed = subprocess.run(command, cwd=PROJECT, env=BASE_ENV, stdin=subprocess.DEVNULL, check=False, close_fds=True)
        child_receipt = paths['child_receipt']
        guard_receipt = paths['guard_receipt']
        child_value: dict[str, Any] | None = None
        guard_value: dict[str, Any] | None = None
        if child_receipt.is_file() and (not child_receipt.is_symlink()):
            child_value = json.loads(child_receipt.read_text(encoding='utf-8'))
        if guard_receipt.is_file() and (not guard_receipt.is_symlink()):
            guard_value = json.loads(guard_receipt.read_text(encoding='utf-8'))
        require_absent(LEASE, 'post-phase canonical managed lease')
        live_after = live_qm8_processes()
        owned_lock.verify()
    finally:
        owned_lock.release()
    require_absent(LEASE, 'released canonical managed lease')
    require_absent(LOCK, 'released canonical managed acquisition lock')
    successful = bool(completed.returncode == 0 and child_value is not None and (guard_value is not None) and child_pass(child_value, args.phase) and guard_pass(guard_value) and (not live_after))
    output = {'schema': 'gamma.enwiki9.safe-mix-v2-activation-receipt.v1', 'candidate_id': CANDIDATE_ID, 'subject_candidate_id': SUBJECT_ID, 'phase': args.phase, 'activation_plan': artifact(plan_path), 'qm8_terminal_receipt': artifact(terminal_path), 'qm8_terminal_classification': artifact(classification_path), 'managed_lease_verification': artifact(lease_verification_path), 'canonical_lease_manager': artifact(canonical_manager), 'owned_lock_witness': lock_witness, 'toolchain_probes': probes, 'source_bindings_sha256': sha256_bytes(canonical(plan['source_bindings'])), 'toolchain_bindings_sha256': sha256_bytes(canonical(plan['activation']['toolchain'])), 'command': command, 'command_sha256': sha256_bytes(canonical(command)), 'return_code': completed.returncode, 'child_receipt': artifact(child_receipt) if child_value is not None else None, 'guard_receipt': artifact(guard_receipt) if guard_value is not None else None, 'namespace_free_before_pass': True, 'namespace_free_after_pass': True, 'no_live_qm8_before_pass': True, 'no_live_qm8_after_pass': not live_after, 'child_terminal_pass': child_value is not None and child_pass(child_value, args.phase), 'resource_guard_pass': guard_value is not None and guard_pass(guard_value), 'terminal_pass': successful, 'execution_authority': False, 'archive_authority': False, 'gamma_compression_credit_bytes': 0, 'gamma_score_credit_bytes': 0}
    write_new(paths['gate_receipt'], output)
    return 0 if successful else 2
if __name__ == '__main__':
    raise SystemExit(main())
