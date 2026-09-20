"""Explicit CPU reference adaptation of pinned upstream FX2 training sources.

This is a development runtime, not a substitute for native finite-archive replay.
Upstream implementation and GPL-3.0 license remain required source dependencies.
No installed packages or upstream files are modified. Derived sources live only
in the caller's owned workspace, with preimage and postimage identities.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


PREIMAGES = {
    "model": "5f8a5dfe8c4db881fdd02bdc7ef6704a506f62d020f803ba348084ccbf3b2052",
    "quantization": "076dba090af4d9bb97c97b411f902fa11d46cc35d00d75f35146a74cf1c708b6",
    "attention_function": "1ac9c5f59d0f881565df23c4d809646f5adbe2eeb42059d3713a4cf82fb6973f",
    "kda_reference": "c34a3a43a0c894400db62bba2c2aebe47544ef9e2bce1a72b8872c275faca5fb",
    "export_weights": "bac19094137e6cea761bf336f178ba55dfee2a12a6cd0dd1d4a88fd95c6df817",
    "weights_compress": "eb3a5404886f4cc8b67a0197385ef1f0f220721707f269fa54870f28ba53e6c8",
}


class _ReferenceImports(ast.NodeTransformer):
    """Use real reference kernels; erase optional shape-typing metadata only."""

    def visit_ImportFrom(self, node):
        if node.module == "jaxtyping":
            return None
        if node.module and node.module.startswith("fla."):
            return ast.copy_location(ast.ImportFrom(
                module="reference_kernels", names=node.names, level=1), node)
        if node.module and node.module.startswith("pysrc."):
            node.module = node.module.removeprefix("pysrc.")
            node.level = 1
        return node

    def visit_Subscript(self, node):
        if isinstance(node.value, ast.Name) and node.value.id in {"Float", "Int", "Bool"}:
            return ast.copy_location(ast.Name(id="Tensor", ctx=ast.Load()), node)
        return self.generic_visit(node)

    def visit_Assign(self, node):
        # SDPA is selected explicitly. Importing this package must not start a
        # compiler or populate global compiler caches for an unused backend.
        if (len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "flex_attention"
                and isinstance(node.value, ast.Call)):
            return None
        return self.generic_visit(node)

    def visit_Call(self, node):
        node = self.generic_visit(node)
        if isinstance(node.func, ast.Name) and node.func.id == "TransformerConfig":
            # Pinned save_outputs.py sets False; the pinned exporter predates
            # this required config field. Strict state loading checks that no
            # learned query/key gain tensors have been invented or discarded.
            if not any(k.arg == "query_key_norm_gain" for k in node.keywords):
                node.keywords.append(ast.keyword(arg="query_key_norm_gain", value=ast.Constant(False)))
        return node


def materialize(upstream: Path, workspace: Path) -> dict:
    """Authenticate all sources before creating a new derived package."""
    sources = {}
    for name, expected in PREIMAGES.items():
        data = (upstream / "pysrc" / f"{name}.py").read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError(f"FX2 source preimage mismatch: {name}")
        sources[name] = data
    license_bytes = (upstream / "LICENSE").read_bytes()
    # A workspace must be new; this cannot overwrite another attempt.
    workspace.mkdir(parents=True, exist_ok=False)
    manifest = {"profile": "fx2_cpu_reference_v1", "sources": {},
                "native_parity": "not_established", "score_credit": 0}
    for name, data in sources.items():
        tree = _ReferenceImports().visit(ast.parse(data))
        derived = (ast.unparse(ast.fix_missing_locations(tree)) + "\n").encode()
        (workspace / f"{name}.py").write_bytes(derived)
        manifest["sources"][name] = {
            "preimage_sha256": PREIMAGES[name],
            "postimage_sha256": hashlib.sha256(derived).hexdigest(),
        }
    kernels = Path(__file__).with_name("fx2_reference_kernels.py").read_bytes()
    (workspace / "reference_kernels.py").write_bytes(kernels)
    (workspace / "LICENSE").write_bytes(license_bytes)
    (workspace / "__init__.py").write_text("")
    manifest["kernel_sha256"] = hashlib.sha256(kernels).hexdigest()
    manifest["license_sha256"] = hashlib.sha256(license_bytes).hexdigest()
    (workspace / "adaptation.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def load_package(workspace: Path):
    """Load a caller-owned adaptation without replacing the global pysrc name."""
    identity = hashlib.sha256(str(workspace.resolve()).encode()).hexdigest()[:20]
    name = f"_gamma_fx2_reference_{identity}"
    if name in sys.modules:
        raise ValueError("adapted package already loaded; use a fresh process")
    spec = importlib.util.spec_from_file_location(name, workspace / "__init__.py",
                                                 submodule_search_locations=[str(workspace)])
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return name


def load_model(package: str, checkpoint: Path):
    """Load the full existing checkpoint strictly, using FP32 reference + SDPA."""
    from dataclasses import replace
    import importlib
    import torch

    exporter = importlib.import_module(package + ".export_weights")
    model_module = importlib.import_module(package + ".model")
    config = replace(exporter.make_reference_config(), attention_implementation="sdpa")
    model = model_module.Transformer(config)
    model.load_state_dict(torch.load(checkpoint, map_location="cpu", weights_only=True), strict=True)
    return model
