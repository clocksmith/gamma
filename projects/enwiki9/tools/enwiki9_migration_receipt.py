#!/usr/bin/env python3
"""Generate an evidence-backed receipt for an enwiki9 host migration.

The tool is read-only apart from its generated Markdown and JSON receipts. It
does not install packages, create filesystems, authorize SSH keys, promote
quarantined corpus files, or create Git worktrees. Those state changes stay
blocked until their required inputs are explicit.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parents[1]
DEFAULT_JSON = PROJECT_ROOT / "docs" / "amd_migration_receipt.json"
DEFAULT_MARKDOWN = PROJECT_ROOT / "docs" / "amd_migration_receipt.md"
DEFAULT_MINIMUM_FREE_BYTES = 128 * 1024**3

STORAGE_BUDGET_BYTES: dict[str, int] = {
    "clean_repo_and_two_worktrees": 16 * 1024**3,
    "corpus_and_source_archive": 2 * 1024**3,
    "mmap_traces": 20 * 1024**3,
    "compressor_scratch": 32 * 1024**3,
    "builds_archives_and_receipts": 16 * 1024**3,
    "free_reserve": 42 * 1024**3,
}

REQUIRED_COMMANDS: dict[str, tuple[str, ...]] = {
    "git": ("git", "--version"),
    "rsync": ("rsync", "--version"),
    "g++": ("g++", "--version"),
    "make": ("make", "--version"),
    "python3": ("python3", "--version"),
    "pip3": ("pip3", "--version"),
    "gzip": ("gzip", "--version"),
    "xz": ("xz", "--version"),
    "sha256sum": ("sha256sum", "--version"),
    "md5sum": ("md5sum", "--version"),
    "b2sum": ("b2sum", "--version"),
    "cksum": ("cksum", "--version"),
    "unzip": ("unzip", "-v"),
    "ssh": ("ssh", "-V"),
}

LAYOUT: dict[str, str] = {
    "proof_checkout": "checkouts/gamma-proof",
    "non_proof_checkout": "checkouts/gamma-non-proof",
    "non_proof_label": "checkouts/NON_PROOF_RESEARCH_ONLY.md",
    "portable_proof_build": "build/portable-proof",
    "native_search_build": "build/native-search",
    "incoming_corpus": "data/incoming-unaccepted",
    "canonical_corpus": "data/canonical",
    "mmap_scratch": "scratch/mmap",
    "compressor_scratch": "scratch/compressor",
    "archives": "archives",
    "receipts": "receipts",
}


def run(command: list[str], *, cwd: Path | None = None) -> dict[str, Any]:
    """Run a read-only probe and preserve its exact output."""

    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
    except OSError as exc:
        return {
            "command": command,
            "returncode": None,
            "output": str(exc),
        }
    return {
        "command": command,
        "returncode": completed.returncode,
        "output": completed.stdout.rstrip(),
    }


def first_line(value: str) -> str:
    return value.splitlines()[0] if value else ""


def command_inventory() -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for name, version_command in REQUIRED_COMMANDS.items():
        executable = shutil.which(name)
        probe = run(list(version_command)) if executable else None
        rows[name] = {
            "present": executable is not None,
            "path": executable,
            "version": first_line(probe["output"]) if probe else None,
            "version_returncode": probe["returncode"] if probe else None,
        }
    missing = [name for name, row in rows.items() if not row["present"]]
    return {
        "all_present": not missing,
        "missing": missing,
        "commands": rows,
    }


def memory_inventory() -> dict[str, Any]:
    meminfo: dict[str, int] = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        key, raw_value = line.split(":", 1)
        fields = raw_value.split()
        if fields and fields[0].isdigit():
            multiplier = 1024 if len(fields) > 1 and fields[1] == "kB" else 1
            meminfo[key] = int(fields[0]) * multiplier
    return {
        "mem_total_bytes": meminfo.get("MemTotal"),
        "mem_available_bytes": meminfo.get("MemAvailable"),
        "swap_total_bytes": meminfo.get("SwapTotal"),
        "swap_free_bytes": meminfo.get("SwapFree"),
        "free_bytes_output": run(["free", "--bytes"])["output"],
    }


def filesystem_inventory() -> dict[str, Any]:
    return {
        "df_bytes": run(
            ["df", "-B1", "-T", "/", "/home", "/tmp", str(PROJECT_ROOT)]
        )["output"],
        "lsblk_bytes": run(
            [
                "lsblk",
                "-b",
                "-o",
                "NAME,KNAME,TYPE,SIZE,FSTYPE,FSVER,MOUNTPOINTS,FSAVAIL,FSUSE%,MODEL",
            ]
        )["output"],
        "findmnt_json": run(
            ["findmnt", "-J", "-o", "TARGET,SOURCE,FSTYPE,OPTIONS"]
        )["output"],
    }


def nearest_existing_path(path: Path) -> Path:
    candidate = path.expanduser().resolve(strict=False)
    while not candidate.exists() and candidate != candidate.parent:
        candidate = candidate.parent
    return candidate


def destination_inventory(
    destination: Path | None, minimum_free_bytes: int
) -> dict[str, Any]:
    if destination is None:
        return {
            "configured": False,
            "path": None,
            "minimum_free_bytes": minimum_free_bytes,
            "ready": False,
            "reason": "AMD_DEST is unset and --destination was not supplied",
            "layout": {},
        }

    destination = destination.expanduser().resolve(strict=False)
    probe_path = nearest_existing_path(destination)
    usage = shutil.disk_usage(probe_path)
    mount = run(["findmnt", "-J", "-T", str(probe_path)])
    layout = {
        name: {
            "path": str(destination / relative),
            "exists": (destination / relative).exists(),
        }
        for name, relative in LAYOUT.items()
    }
    ready = destination.exists() and usage.free >= minimum_free_bytes
    if not destination.exists():
        reason = "destination directory does not exist"
    elif usage.free < minimum_free_bytes:
        reason = "destination filesystem is below the minimum free-byte gate"
    else:
        reason = "destination exists and clears the free-byte gate"
    return {
        "configured": True,
        "path": str(destination),
        "exists": destination.exists(),
        "probe_path": str(probe_path),
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
        "minimum_free_bytes": minimum_free_bytes,
        "ready": ready,
        "reason": reason,
        "mount_probe": mount,
        "layout": layout,
    }


def hash_file(path: Path) -> dict[str, Any]:
    digests = {
        "md5": hashlib.md5(usedforsecurity=False),
        "sha256": hashlib.sha256(),
        "blake2b": hashlib.blake2b(),
    }
    with path.open("rb") as stream:
        while chunk := stream.read(8 * 1024 * 1024):
            for digest in digests.values():
                digest.update(chunk)
    return {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        **{name: digest.hexdigest() for name, digest in digests.items()},
    }


def manifest_entries(payload: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(payload, dict):
        raise ValueError("source manifest must be a JSON object")
    files = payload.get("files")
    if isinstance(files, list):
        result: dict[str, dict[str, Any]] = {}
        for row in files:
            if not isinstance(row, dict):
                continue
            name = row.get("name") or row.get("path")
            if isinstance(name, str):
                result[Path(name).name] = row
        return result
    return {
        name: payload[name]
        for name in ("enwik9.zip", "enwik9")
        if isinstance(payload.get(name), dict)
    }


def compare_manifest(
    observed: dict[str, dict[str, Any]], manifest_path: Path | None
) -> dict[str, Any]:
    if manifest_path is None:
        return {
            "status": "pending_source_manifest",
            "accepted": False,
            "manifest_path": None,
            "comparisons": {},
        }
    manifest_path = manifest_path.expanduser().resolve(strict=False)
    if not manifest_path.is_file():
        return {
            "status": "source_manifest_missing",
            "accepted": False,
            "manifest_path": str(manifest_path),
            "comparisons": {},
        }
    try:
        entries = manifest_entries(json.loads(manifest_path.read_text()))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return {
            "status": "source_manifest_invalid",
            "accepted": False,
            "manifest_path": str(manifest_path),
            "error": str(exc),
            "comparisons": {},
        }

    comparisons: dict[str, Any] = {}
    all_match = True
    for name in ("enwik9.zip", "enwik9"):
        actual = observed.get(name)
        expected = entries.get(name)
        row: dict[str, Any] = {
            "observed": actual,
            "expected": expected,
            "match": False,
        }
        if actual and expected:
            size = expected.get("size_bytes", expected.get("size"))
            sha256 = expected.get("sha256")
            md5 = expected.get("md5")
            required_match = size == actual["size_bytes"] and sha256 == actual["sha256"]
            optional_md5_match = md5 is None or md5 == actual["md5"]
            row["match"] = required_match and optional_md5_match
        comparisons[name] = row
        all_match = all_match and row["match"]
    return {
        "status": "accepted" if all_match else "source_manifest_mismatch",
        "accepted": all_match,
        "manifest_path": str(manifest_path),
        "comparisons": comparisons,
    }


def corpus_inventory(
    quarantine: Path | None, manifest_path: Path | None
) -> dict[str, Any]:
    observed: dict[str, dict[str, Any]] = {}
    if quarantine is not None:
        quarantine = quarantine.expanduser().resolve(strict=False)
        for name in ("enwik9.zip", "enwik9"):
            path = quarantine / name
            if path.is_file():
                observed[name] = hash_file(path)
    comparison = compare_manifest(observed, manifest_path)
    return {
        "quarantine_path": str(quarantine) if quarantine else None,
        "observed": observed,
        "archive_integrity": (
            run(["unzip", "-t", str(quarantine / "enwik9.zip")])
            if quarantine and (quarantine / "enwik9.zip").is_file()
            else None
        ),
        "source_manifest": comparison,
        "canonical_promotion_allowed": comparison["accepted"],
    }


def ssh_inventory(
    amd_host: str | None,
    amd_user: str | None,
    destination: Path | None,
    probe_ssh: bool,
) -> dict[str, Any]:
    authorized_keys = Path.home() / ".ssh" / "authorized_keys"
    configured = bool(amd_host and amd_user and destination)
    probe: dict[str, Any] | None = None
    if probe_ssh and amd_host and amd_user:
        probe = run(
            [
                "ssh",
                "-o",
                "BatchMode=yes",
                "-o",
                "ConnectTimeout=8",
                f"{amd_user}@{amd_host}",
                "id -un; hostname; pwd",
            ]
        )
    return {
        "amd_host": amd_host,
        "amd_user": amd_user,
        "destination": str(destination) if destination else None,
        "identity_configured": configured,
        "sshd_enabled": run(["systemctl", "is-enabled", "ssh.service"]),
        "sshd_active": run(["systemctl", "is-active", "ssh.service"]),
        "port_22_listeners": run(["ss", "-ltn", "sport = :22"]),
        "authorized_keys_path": str(authorized_keys),
        "authorized_keys_bytes": authorized_keys.stat().st_size
        if authorized_keys.exists()
        else None,
        "probe_requested": probe_ssh,
        "probe": probe,
        "verified": bool(configured and probe and probe["returncode"] == 0),
    }


def workspace_inventory() -> dict[str, Any]:
    return {
        "repo_root": str(REPO_ROOT),
        "project_root": str(PROJECT_ROOT),
        "git_head": run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT),
        "git_status": run(["git", "status", "--short", "--branch"], cwd=REPO_ROOT),
        "git_worktrees": run(["git", "worktree", "list", "--porcelain"], cwd=REPO_ROOT),
        "repo_du_bytes": run(["du", "-sb", str(REPO_ROOT)]),
        "project_du_bytes": run(["du", "-sb", str(PROJECT_ROOT)]),
        "tracked_bytes": run(
            [
                "bash",
                "-lc",
                "git ls-files -z | du --files0-from=- -cb | tail -n 1",
            ],
            cwd=REPO_ROOT,
        ),
    }


def proof_artifact_inventory() -> dict[str, Any]:
    audit_path = PROJECT_ROOT / "docs" / "artifact_fingerprint_audit.json"
    status_path = PROJECT_ROOT / "docs" / "status_receipt.json"
    audit: dict[str, Any] = {}
    status: dict[str, Any] = {}
    try:
        audit = json.loads(audit_path.read_text())
    except (OSError, json.JSONDecodeError):
        pass
    try:
        status = json.loads(status_path.read_text())
    except (OSError, json.JSONDecodeError):
        pass
    candidate_audit = status.get("candidate_audit")
    return {
        "fingerprint_audit_path": str(audit_path),
        "fingerprint_audit_present": bool(audit),
        "fingerprint_audit_ok": audit.get("ok"),
        "fingerprint_status_counts": audit.get("status_counts", {}),
        "candidate_audit": candidate_audit,
        "candidate_audit_ok": isinstance(candidate_audit, dict)
        and candidate_audit.get("returncode") == 0,
    }


def build_blockers(receipt: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if not receipt["tooling"]["all_present"]:
        blockers.append("required_packages_missing")
    if not receipt["destination"]["ready"]:
        blockers.append("destination_filesystem_not_ready")
    if not receipt["ssh"]["identity_configured"]:
        blockers.append("amd_host_user_or_destination_unset")
    elif not receipt["ssh"]["verified"]:
        blockers.append("ssh_access_not_verified")
    if not receipt["corpus"]["source_manifest"]["accepted"]:
        blockers.append("corpus_waiting_for_source_manifest")
    if receipt["proof_artifacts"]["fingerprint_audit_ok"] is not True:
        blockers.append("proof_receipt_artifacts_not_migrated")
    if receipt["proof_artifacts"]["candidate_audit_ok"] is not True:
        blockers.append("candidate_audit_not_clean")
    layout = receipt["destination"].get("layout", {})
    if not layout or not all(row["exists"] for row in layout.values()):
        blockers.append("proof_search_layout_not_prepared")
    non_proof = layout.get("non_proof_checkout")
    label = layout.get("non_proof_label")
    if not non_proof or not label or not (non_proof["exists"] and label["exists"]):
        blockers.append("non_proof_checkout_not_prepared_or_labeled")
    return blockers


def build_receipt(args: argparse.Namespace) -> dict[str, Any]:
    destination = Path(args.destination) if args.destination else None
    quarantine = Path(args.quarantine) if args.quarantine else None
    manifest = Path(args.source_manifest) if args.source_manifest else None
    receipt: dict[str, Any] = {
        "schema_version": 1,
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "receipt_type": "enwiki9_amd_host_migration",
        "proof_boundary": "infrastructure receipt only; no compression score claim",
        "host": {
            "hostname": platform.node(),
            "user": os.environ.get("USER"),
            "platform": platform.platform(),
            "kernel": run(["uname", "-a"]),
            "lscpu": run(["lscpu"]),
            "lscpu_e": run(["lscpu", "-e"]),
            "memory": memory_inventory(),
            "python": {
                "executable": sys.executable,
                "version": sys.version,
            },
            "compiler": run(["g++", "--version"]),
            "os_release": Path("/etc/os-release").read_text().rstrip(),
        },
        "tooling": command_inventory(),
        "filesystems": filesystem_inventory(),
        "destination": destination_inventory(
            destination, args.minimum_free_bytes
        ),
        "ssh": ssh_inventory(
            args.amd_host, args.amd_user, destination, args.probe_ssh
        ),
        "corpus": corpus_inventory(quarantine, manifest),
        "workspace": workspace_inventory(),
        "proof_artifacts": proof_artifact_inventory(),
        "storage_budget_bytes": STORAGE_BUDGET_BYTES,
    }
    receipt["blockers"] = build_blockers(receipt)
    receipt["ready"] = not receipt["blockers"]
    return receipt


def render_markdown(receipt: dict[str, Any]) -> str:
    tooling = receipt["tooling"]
    destination = receipt["destination"]
    ssh = receipt["ssh"]
    corpus = receipt["corpus"]
    workspace = receipt["workspace"]
    proof_artifacts = receipt["proof_artifacts"]
    lines = [
        "# AMD enwiki9 Migration Receipt",
        "",
        "Generated from live host, toolchain, filesystem, SSH, and corpus probes.",
        "",
        f"- Generated at UTC: `{receipt['generated_at_utc']}`",
        f"- Ready: `{str(receipt['ready']).lower()}`",
        f"- Proof boundary: `{receipt['proof_boundary']}`",
        "",
        "## Blockers",
        "",
    ]
    if receipt["blockers"]:
        lines.extend(f"- `{blocker}`" for blocker in receipt["blockers"])
    else:
        lines.append("- `none`")

    lines.extend(
        [
            "",
            "## Host",
            "",
            f"- Hostname: `{receipt['host']['hostname']}`",
            f"- User: `{receipt['host']['user']}`",
            f"- Python executable: `{receipt['host']['python']['executable']}`",
            f"- Python version: `{first_line(receipt['host']['python']['version'])}`",
            "",
            "### `lscpu -e`",
            "",
            "```text",
            receipt["host"]["lscpu_e"]["output"],
            "```",
            "",
            "### RAM",
            "",
            "```text",
            receipt["host"]["memory"]["free_bytes_output"],
            "```",
            "",
            "### Kernel",
            "",
            "```text",
            receipt["host"]["kernel"]["output"],
            "```",
            "",
            "### Compiler",
            "",
            "```text",
            receipt["host"]["compiler"]["output"],
            "```",
            "",
            "## Tooling",
            "",
            f"- All requested commands present: `{str(tooling['all_present']).lower()}`",
            "",
            "| Command | Present | Path | Version |",
            "|---|---|---|---|",
        ]
    )
    for name, row in tooling["commands"].items():
        version = (row["version"] or "n/a").replace("|", "\\|")
        lines.append(
            f"| `{name}` | `{str(row['present']).lower()}` | "
            f"`{row['path'] or 'n/a'}` | `{version}` |"
        )

    lines.extend(
        [
            "",
            "## Filesystems",
            "",
            "```text",
            receipt["filesystems"]["df_bytes"],
            "```",
            "",
            "### Storage basis",
            "",
            f"- Current working tree `du -sb`: `{workspace['repo_du_bytes']['output']}`",
            f"- Current enwiki9 subtree `du -sb`: `{workspace['project_du_bytes']['output']}`",
            f"- Current tracked files: `{workspace['tracked_bytes']['output']}`",
            "- The 128 GiB gate budgets a clean checkout plus two working trees, corpus",
            "  and source archive, mmap traces, compressor scratch, build/archive/receipt",
            "  space, and a free reserve. It does not budget a byte-for-byte copy of the",
            "  current working tree's unrelated generated project artifacts.",
            "",
            "## Destination",
            "",
            f"- Configured: `{str(destination['configured']).lower()}`",
            f"- Path: `{destination.get('path') or 'unset'}`",
            f"- Minimum free bytes: `{destination['minimum_free_bytes']}`",
            f"- Ready: `{str(destination['ready']).lower()}`",
            f"- Reason: `{destination['reason']}`",
            "",
            "Required layout:",
            "",
        ]
    )
    if destination.get("layout"):
        for name, row in destination["layout"].items():
            lines.append(
                f"- `{name}`: `{row['path']}`; exists=`{str(row['exists']).lower()}`"
            )
    else:
        for name, relative in LAYOUT.items():
            lines.append(f"- `{name}`: `<AMD_DEST>/{relative}`")

    lines.extend(
        [
            "",
            "## SSH",
            "",
            f"- AMD_HOST: `{ssh['amd_host'] or 'unset'}`",
            f"- AMD_USER: `{ssh['amd_user'] or 'unset'}`",
            f"- Destination: `{ssh['destination'] or 'unset'}`",
            f"- Identity configured: `{str(ssh['identity_configured']).lower()}`",
            f"- Authorized keys bytes on this host: `{ssh['authorized_keys_bytes']}`",
            f"- Verified: `{str(ssh['verified']).lower()}`",
            "",
            "## Proof Artifact Migration",
            "",
            f"- Fingerprint audit OK: `{str(proof_artifacts['fingerprint_audit_ok']).lower()}`",
            f"- Fingerprint status counts: `{json.dumps(proof_artifacts['fingerprint_status_counts'], sort_keys=True)}`",
            f"- Candidate audit OK: `{str(proof_artifacts['candidate_audit_ok']).lower()}`",
            "",
            "## Corpus Quarantine",
            "",
            f"- Quarantine: `{corpus['quarantine_path'] or 'unset'}`",
            f"- Manifest status: `{corpus['source_manifest']['status']}`",
            f"- Accepted: `{str(corpus['source_manifest']['accepted']).lower()}`",
            f"- Canonical promotion allowed: `{str(corpus['canonical_promotion_allowed']).lower()}`",
            "",
            "| File | Bytes | MD5 | SHA256 | BLAKE2b |",
            "|---|---:|---|---|---|",
        ]
    )
    for name in ("enwik9.zip", "enwik9"):
        row = corpus["observed"].get(name)
        if row:
            lines.append(
                f"| `{name}` | {row['size_bytes']} | `{row['md5']}` | "
                f"`{row['sha256']}` | `{row['blake2b']}` |"
            )
        else:
            lines.append(f"| `{name}` | n/a | n/a | n/a | n/a |")

    lines.extend(
        [
            "",
            "## Next Commands",
            "",
            "Do not run these with placeholders. Supply the intended values first.",
            "",
            "```bash",
            "export AMD_HOST=<host-or-tailnet-name>",
            "export AMD_USER=<remote-user>",
            "export AMD_DEST=<dedicated-mounted-path>",
            "ssh -o BatchMode=yes \"${AMD_USER}@${AMD_HOST}\" 'id -un; hostname; pwd'",
            "python3 projects/enwiki9/tools/enwiki9_migration_receipt.py \\",
            "  --amd-host \"$AMD_HOST\" --amd-user \"$AMD_USER\" \\",
            "  --destination \"$AMD_DEST\" --probe-ssh \\",
            "  --quarantine <independent-quarantine> \\",
            "  --source-manifest <source-manifest.json>",
            "```",
            "",
            "The corpus remains unaccepted until the supplied source manifest matches",
            "both file sizes and SHA256 values. A manifest MD5, when present, must also",
            "match. The receipt tool never promotes quarantine files automatically.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--amd-host", default=os.environ.get("AMD_HOST"))
    parser.add_argument("--amd-user", default=os.environ.get("AMD_USER"))
    parser.add_argument(
        "--destination",
        default=os.environ.get("AMD_DEST") or os.environ.get("AMD_DESTINATION"),
    )
    parser.add_argument("--quarantine", default=os.environ.get("ENWIKI9_QUARANTINE"))
    parser.add_argument(
        "--source-manifest", default=os.environ.get("ENWIKI9_SOURCE_MANIFEST")
    )
    parser.add_argument("--probe-ssh", action="store_true")
    parser.add_argument(
        "--minimum-free-bytes", type=int, default=DEFAULT_MINIMUM_FREE_BYTES
    )
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    receipt = build_receipt(args)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    args.markdown_output.write_text(render_markdown(receipt))
    print(f"wrote {args.json_output}")
    print(f"wrote {args.markdown_output}")
    print(f"ready={str(receipt['ready']).lower()}")
    for blocker in receipt["blockers"]:
        print(f"blocker={blocker}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
