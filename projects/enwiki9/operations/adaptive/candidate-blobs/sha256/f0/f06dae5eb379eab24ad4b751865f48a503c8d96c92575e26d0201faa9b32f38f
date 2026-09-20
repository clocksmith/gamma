"""Fresh-checkpoint native forward with an explicitly separate surrogate backward.

The predictor source is unmodified. Every call exports current model tensors and
runs the native model in a fresh bounded child. Captured predictions are never
an input. Forward logits AND probabilities use native bytes; the differentiable
reference supplies only an approximate Jacobian, not native intermediate state.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib
import json
from pathlib import Path
import re
import subprocess

from .fx2_training_capture import source_members, validate_rows
from .fx2_weight_training import export_entries


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def build(source_zip: Path, harness: Path, workspace: Path, compiler: Path):
    """Build only authenticated native inference sources in a new owned workspace."""
    members = source_members(source_zip)
    workspace.mkdir(parents=True, exist_ok=False)
    sources = {}
    for name, data in members.items():
        if name.startswith('cpp_infer/src/'):
            path = workspace / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            sources[name] = hashlib.sha256(data).hexdigest()
    infer = workspace / 'cpp_infer/src'
    units = [infer / 'weights_io.cpp', infer / 'weights_io_compressed.cpp']
    units += [infer / 'opt' / (name + '.cpp') for name in
              ('qmat_dense', 'qmat_sparse', 'attn', 'kda', 'glue', 'arena_build', 'model_opt')]
    binary = workspace / 'native-forward'
    command = [str(compiler), '-std=c++17', '-O3', '-march=x86-64-v3',
               '-mrecip=none', '-fno-math-errno', '-I', str(workspace),
               str(harness), *map(str, units), '-o', str(binary)]
    with (workspace / 'build.stdout').open('xb') as out, (workspace / 'build.stderr').open('xb') as err:
        subprocess.run(command, check=True, timeout=120, stdout=out, stderr=err)
    manifest = {'source_zip_sha256': digest(source_zip), 'sources': sources,
                'source_mutations': [], 'harness_sha256': digest(harness),
                'compiler_sha256': digest(compiler), 'command': command,
                'binary_sha256': digest(binary)}
    (workspace / 'build.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return binary, manifest


def attach_native_values(surrogate, native):
    """Exact native forward, identity adjoint into the named surrogate graph.

Do not use x + (native-x).detach(): cancellation can alter the forward bits.
This is a whole-reference surrogate Jacobian, NOT an exact native derivative.
"""
    import torch
    if surrogate.shape != native.shape or surrogate.dtype != native.dtype or surrogate.device != native.device:
        raise ValueError('native/surrogate tensor geometry differs')
    if native.requires_grad:
        raise ValueError('native observations must be detached')

    class NativeValue(torch.autograd.Function):
        @staticmethod
        def forward(ctx, approximate, actual):
            return actual.clone()

        @staticmethod
        def backward(ctx, upstream):
            return upstream, None

    return NativeValue.apply(surrogate, native)


def reference_logits(model, tokens, markers, priors):
    """Differentiable reference on the exact same declared pieces as native."""
    import torch
    parts = []
    start = 0
    while start < len(tokens):
        if markers[start] == 2:
            parts.append(torch.zeros((1, 205), dtype=torch.float32))
            start += 1
            continue
        end = start + 1
        while end < len(tokens) and markers[end] != 2:
            end += 1
        piece = model.compute_logits(torch.tensor(tokens[start:end].tolist(), dtype=torch.long).reshape(1, -1),
            torch.tensor(priors[start:end].astype('float32')).unsqueeze(0),
            torch.tensor([[0, end-start]], dtype=torch.int32))[0]
        parts.append(piece)
        start = end
    return torch.cat(parts)


@dataclass(frozen=True)
class ForwardResult:
    logits: object
    probabilities: object
    rows: dict
    receipt: dict

    def loss_bits(self, tokens, markers):
        """Neural truth loss, never an archive-byte or final-mixer objective."""
        import numpy as np
        import torch
        if hashlib.sha256(np.stack((tokens, markers), axis=1).tobytes()).hexdigest() != self.receipt['tokens_markers_sha256']:
            raise ValueError('loss population differs from native forward inputs')
        indices = np.flatnonzero(markers[:-1] != 2)
        if not len(indices):
            raise ValueError('no paired truth positions')
        truth = self.probabilities[torch.tensor(indices), torch.tensor(tokens[indices+1].astype('int64'))]
        if not torch.isfinite(truth).all() or (truth <= 0).any() or (truth > 1).any():
            raise ValueError('invalid native truth probability')
        return -truth.double().log2().sum()


class NativeForward:
    """Explicit binary/workspace dependency; no repository or checkpoint discovery."""
    def __init__(self, binary: Path, binary_sha256: str, workspace: Path, *, timeout_seconds=120):
        self.binary = binary.resolve()
        self.binary_sha256 = binary_sha256
        self.workspace = workspace.resolve()
        self.timeout = timeout_seconds
        self.workspace.mkdir(parents=True, exist_ok=False)

    def __call__(self, model, template, package, tokens, markers, priors, *, label, surrogate_backward=False):
        import numpy as np
        import torch
        if not re.fullmatch(r'[A-Za-z0-9_-]+', label):
            raise ValueError('invalid invocation identity')
        if tokens.dtype != np.uint8 or markers.dtype != np.uint8 or tokens.ndim != 1 or markers.shape != tokens.shape:
            raise ValueError('tokens and markers must be explicit uint8 vectors')
        if priors.dtype != np.dtype('<f2') or priors.shape != (len(tokens), 205) or not np.isfinite(priors).all():
            raise ValueError('priors must be finite native FP16 rows')
        pairs = np.stack((tokens, markers), axis=1)
        rows = validate_rows(pairs.tobytes(), priors.nbytes)
        if digest(self.binary) != self.binary_sha256:
            raise ValueError('native binary identity changed')
        if any(p.device.type != 'cpu' for p in model.parameters()):
            raise ValueError('native forward profile requires CPU parameters')
        call = self.workspace / label
        call.mkdir(exist_ok=False)
        entries = export_entries(model, template, package)
        weights = call / 'current.weights'
        importlib.import_module(package + '.export_weights').write_tensor_file(str(weights), entries)
        pairs.tofile(call / 'tokens-markers.bin')
        priors.tofile(call / 'priors.f16')
        command = [str(self.binary), str(weights), str(call/'tokens-markers.bin'),
                   str(call/'priors.f16'), str(call/'predictions.f32')]
        with (call/'stdout').open('xb') as out, (call/'stderr').open('xb') as err:
            subprocess.run(command, check=True, timeout=self.timeout, stdout=out, stderr=err)
        values = np.fromfile(call/'predictions.f32', dtype='<f4')
        if values.size != len(tokens)*410 or not np.isfinite(values).all():
            raise ValueError('native output geometry or finiteness differs')
        values = values.reshape(-1, 410)
        logits = torch.from_numpy(values[:, :205].copy())
        probabilities = torch.from_numpy(values[:, 205:].copy())
        if surrogate_backward:
            training = model.training
            try:
                model.eval()
                approximate = reference_logits(model, tokens, markers, priors)
            finally:
                model.train(training)
            logits = attach_native_values(approximate, logits)
            # This Jacobian is Torch softmax at native logits; the forward value
            # remains the actual native softmax, including native math semantics.
            probabilities = attach_native_values(logits.softmax(-1), probabilities)
        receipt = {'command': command, 'binary_sha256': self.binary_sha256,
                   'weights_sha256': digest(weights), 'prediction_sha256': digest(call/'predictions.f32'),
                   'rows': rows, 'surrogate_backward': surrogate_backward,
                   'tokens_markers_sha256': digest(call/'tokens-markers.bin'),
                   'priors_sha256': digest(call/'priors.f16'),
                   'backward_semantics': 'reference model Jacobian and Torch softmax Jacobian at native logits; approximate, not native differentiation',
                   'exported_tensors': [{'name': n, 'kind': k, 'shape': list(a.shape),
                      'sha256': hashlib.sha256(a.tobytes()).hexdigest()} for n,k,a in entries]}
        (call/'forward.json').write_text(json.dumps(receipt, indent=2)+'\n')
        return ForwardResult(logits, probabilities, rows, receipt)
