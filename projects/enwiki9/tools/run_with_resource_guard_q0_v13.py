#!/usr/bin/env python3
"""V13 zero-swap guard with local inherited-chain verification before import."""

import hashlib
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
PREIMPORT_GUARD_DEPENDENCIES = (
    (
        "resource_guard_v12_base",
        "tools/run_with_resource_guard_q0_v12.py",
        780,
        "3994b984eb221c2170446ab98c7762e2ab2b4342976798072315de0ff4f338c8",
    ),
    (
        "resource_guard_v11_base",
        "tools/run_with_resource_guard_q0_v11.py",
        3703,
        "5db7e2927437b1613c06bbbbebcd869de75dfa53463aed30ce2e19b37c53f46a",
    ),
    (
        "resource_guard_v10_base",
        "tools/run_with_resource_guard_q0_v10.py",
        31905,
        "6b1bff8c9a7c00278cbce04713a3ce759ad89ee0041da7d05adc1dea1c93ea57",
    ),
)


def _sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(8 << 20)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _verify_preimport_guard_dependencies():
    observed = {}
    for name, relative, expected_bytes, expected_sha256 in PREIMPORT_GUARD_DEPENDENCIES:
        unresolved = PROJECT / relative
        if unresolved.is_symlink():
            raise RuntimeError(f"pre-import guard dependency cannot be a symlink: {name}")
        try:
            path = unresolved.resolve(strict=True)
        except FileNotFoundError as exc:
            raise RuntimeError(f"pre-import guard dependency missing: {name}") from exc
        if path != unresolved.absolute():
            raise RuntimeError(f"pre-import guard dependency escaped exact path: {name}")
        stat = path.stat()
        digest = _sha256_file(path)
        if stat.st_size != expected_bytes or digest != expected_sha256:
            raise RuntimeError(f"pre-import guard dependency drift: {name}")
        observed[name] = {
            "path": relative,
            "bytes": stat.st_size,
            "sha256": digest,
        }
    return {
        "policy": "hardcoded-stdlib-path-bytes-sha256-before-dynamic-import-v1",
        "artifact_count": len(observed),
        "verified_before_dynamic_import": True,
        "artifacts": observed,
    }


PREIMPORT_GUARD_REPORT = _verify_preimport_guard_dependencies()

# No inherited guard is imported or executed above this boundary.
import importlib.util
from typing import Any


V12_PATH = PROJECT / "tools/run_with_resource_guard_q0_v12.py"


def _load(path: Path, name: str) -> Any:
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


V12 = _load(V12_PATH, "cmix_q0_v13_guard_v12_base")


def main() -> int:
    return V12.main()


if __name__ == "__main__":
    raise SystemExit(main())
