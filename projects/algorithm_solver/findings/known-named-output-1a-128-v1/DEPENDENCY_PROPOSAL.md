# SortedList dependency proposal — not executed

Fifteen remaining entries fail because `SortedList` / `sortedcontainers` is unavailable. Every selected reference uses `SortedList`: fourteen omit an import and one explicitly imports it. All 27 existing indexed reference alternatives also depend on it. Sources contain **no version pin**, and the earlier local dependency/installed-distribution/named-cache scan found no available artifact. `dependency-source-census.json` records selected source identities and imports.

Proposed artifact, verified from [official PyPI release JSON](https://pypi.org/pypi/sortedcontainers/2.4.0/json):

| Field | Value |
|---|---|
| Package/version | `sortedcontainers==2.4.0` |
| Wheel | `sortedcontainers-2.4.0-py2.py3-none-any.whl` |
| Size | 29,575 bytes |
| SHA256 | `a163dcaede0f1c021485e957a39245190e74249897e2ae4b2aa38595db237ee0` |
| License | Apache-2.0 |
| Declared dependencies | None (`requires_dist: null`) |
| Wheel URL | `https://files.pythonhosted.org/packages/32/46/9cb0e58b2deb7f82b84065f37f3bffeb12413f947f9388e4cac22c4621ce/sortedcontainers-2.4.0-py2.py3-none-any.whl` |

The project describes a pure-Python implementation. This is a concrete proposed version, not a historically required version or demonstrated Python3.14 compatibility result. Only metadata was browsed; **no wheel/source archive was downloaded, installed, extracted or executed**.

## Reproducible integration after separate approval

The existing judge executes `/usr/bin/python3 -I -S`, so host venv installation and merely placing an unpacked package under `/task` cannot make it importable. Isolated mode excludes the script/current directory from module search, and the current sandbox writer explicitly rejects nested task filenames.

A proposed integration can retain those restrictions:

1. After explicit dependency/judge-integration approval, acquire the exact wheel, check byte count and SHA256, inspect its Python modules and license, and freeze the archive/member manifest. Reject unexpected packages, path traversal, absolute paths, symlink-like entries and native extensions. Do not run a package installer or setup script.
2. Supply the intact wheel as one fixed **flat** task file, for example `/task/vendor-sortedcontainers-2.4.0.whl`. This fits the existing flat `files` mapping; the wheel's nested package files stay inside the ZIP. No new filesystem write permission, mount or recursive task-file support is required.
3. Add a narrow, opt-in, manifest-bound harness bootstrap before candidate source execution. Use a `zipimport.zipimporter` for that exact wheel, obtain the `sortedcontainers` package spec, create/register the module using `importlib.util.module_from_spec` and `sys.modules`, then execute its loader. Relative package imports resolve through that explicit package spec. Do not rely on cwd, `PYTHONPATH`, site initialization or an arbitrary manifest-selected import path. This exact bootstrap must be tested on the current isolated interpreter before any qualification claim.
4. Bind the loaded package's `SortedList` into the candidate namespace (`ns['SortedList']`) for the fourteen references that omit the convenience import. The one explicit import then resolves the preloaded package. Candidate source bytes remain unchanged; bootstrap/package identities become part of the new judge contract.
5. Keep `-I -S`, network isolation, read-only `/usr` and `/task`, expected-output separation, namespace restrictions, process/file/CPU/memory limits, and monitor integrity unchanged. Run focused sandbox tests plus a frozen fifteen-case paired comparison: public decisions first, then existing independent tests, with no assumed fifteen-case success.

This needs explicit **dependency acquisition and judge-integration approval**, distinct from training approval. A newly bound candidate catalog would require fresh relevant execution and regression verification; the current catalogs must remain intact. The proposal is not an instruction to weaken security policy or perform a global installation.
