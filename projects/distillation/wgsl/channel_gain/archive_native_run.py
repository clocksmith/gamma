#!/usr/bin/env python3
"""Archive/restore completed native run outputs without model or oracle access.

archive --selection-dir DIR --confirmation-dir DIR --output ARCHIVE
restore --archive ARCHIVE --output RESTORED
verify --archive ARCHIVE

Files over 100,000,000 bytes become deterministic gzip streams split into parts
of at most 50,000,000 bytes. Other files retain their exact original bytes.
Restoration concatenates each manifest-ordered part list before gzip decoding.
The restored journals can be passed directly to assemble_confirmation_evidence.
All outputs must be new directories; input files are never changed.
"""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
import zlib

SCHEMA = "gamma.channel-gain-native-archive/v1"
GIT_SAFE_BYTES = 100_000_000
PART_BYTES = 50_000_000
BLOCK_BYTES = 1024 * 1024


def digest(data):
    return hashlib.sha256(data).hexdigest()


def safe_path(root, relative):
    path = PurePosixPath(relative)
    if path.is_absolute() or not path.parts or any(p in (".", "..") or "\\" in p for p in path.parts):
        raise ValueError(f"Unsafe relative path: {relative}")
    target = root.joinpath(*path.parts)
    for parent in [target, *target.parents]:
        if parent == root.parent:
            break
        if parent.is_symlink():
            raise ValueError(f"Symlink is not an archive artifact: {parent}")
    target.resolve().relative_to(root.resolve())
    return target


def files_in(root):
    files = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"Refusing symlink: {path}")
        if path.is_file():
            if path.name.endswith("oracle-checks.json") or path.name in ("references.json", "prompts.jsonl"):
                raise ValueError("Only native run output directories are accepted; oracle/task inputs are excluded")
            files.append(path)
    return files


def fingerprint(path):
    stat = path.stat()
    return (stat.st_size, stat.st_mtime_ns, stat.st_ino)


def completed_receipts(selection, confirmation):
    paths = [selection / "selection-receipt.json", confirmation / "confirmation-receipt.json"]
    values = [json.loads(path.read_bytes()) for path in paths]
    s, c = values
    if (s.get("status") != "selection_complete" or not s.get("requests")
            or c.get("status") != "confirmation_executed" or c.get("confirmationEvaluated") is not True
            or not c.get("generated", {}).get("requests") or not c.get("receipts")
            or not c.get("submissionLock", {}).get("submissions")):
        raise ValueError("Both selection and confirmation must have complete terminal receipts")
    for key in ("runtimeLockSha256", "stageLockSha256"):
        if not re.fullmatch(r"[a-f0-9]{64}", s.get(key, "")) or s[key] != c.get(key):
            raise ValueError(f"Receipt identity mismatch: {key}")
    if (s.get("selectedCandidate") != c.get("selection", {}).get("selectedCandidate")
            or s.get("receiptSha256") != c.get("selection", {}).get("receiptSha256")
            or s.get("continuationSha256") != c.get("continuationSha256")):
        raise ValueError("Confirmation is not bound to this completed selection")
    # Match the writer's JavaScript canonical-number serialization exactly.
    script = """import {readFile} from 'node:fs/promises';import {createHash} from 'node:crypto';
const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
for(const path of process.argv.slice(1)){const {receiptSha256,...body}=JSON.parse(await readFile(path,'utf8'));if(createHash('sha256').update(JSON.stringify(canonical(body))).digest('hex')!==receiptSha256)throw Error('Terminal receipt checksum mismatch: '+path);}
"""
    subprocess.run(["node", "--input-type=module", "-e", script, *map(str, paths)], check=True, capture_output=True)
    return {"selectionRequests": len(s["requests"]), "confirmationRequests": len(c["generated"]["requests"]),
            "runtimeLockSha256": s["runtimeLockSha256"], "stageLockSha256": s["stageLockSha256"],
            "selectionReceiptSha256": s["receiptSha256"], "confirmationReceiptSha256": c["receiptSha256"],
            "continuationSha256": s.get("continuationSha256")}


def find_references(value):
    if isinstance(value, dict):
        if value.get("rawEvidence") is not None:
            if not isinstance(value["rawEvidence"], dict):
                raise ValueError("Malformed rawEvidence reference")
            yield value["rawEvidence"]
        for key, child in value.items():
            if key != "rawEvidence":
                yield from find_references(child)
    elif isinstance(value, list):
        for child in value:
            yield from find_references(child)


def verify_raw_references(roots):
    checked, references = set(), []
    for role, root in roots.items():
        for document in files_in(root):
            if document.suffix != ".json":
                continue
            for ref in find_references(json.loads(document.read_bytes())):
                journal = safe_path(root, ref.get("path", ""))
                offset, length = ref.get("byteOffset"), ref.get("byteLength")
                if (type(offset) is not int or offset < 0 or type(length) is not int or length <= 0
                        or not re.fullmatch(r"[a-f0-9]{64}", ref.get("sha256", ""))):
                    raise ValueError("Malformed rawEvidence offsets/hash")
                key = (str(journal), offset, length, ref["sha256"])
                if key not in checked:
                    hasher, remaining = hashlib.sha256(), length
                    with journal.open("rb") as stream:
                        stream.seek(offset)
                        while remaining:
                            chunk = stream.read(min(BLOCK_BYTES, remaining))
                            if not chunk:
                                raise ValueError("rawEvidence range extends beyond journal")
                            hasher.update(chunk)
                            remaining -= len(chunk)
                    if hasher.hexdigest() != ref["sha256"]:
                        raise ValueError("rawEvidence journal slice checksum mismatch")
                    checked.add(key)
                references.append({"document": f"{role}/{document.relative_to(root).as_posix()}",
                                   "journal": f"{role}/{ref['path']}", "byteOffset": offset, "byteLength": length,
                                   "sha256": ref["sha256"], "line": ref.get("line")})
    return {"references": references, "referenceCount": len(references), "uniqueSlicesVerified": len(checked)}


class PartWriter:
    def __init__(self, root, prefix, limit):
        self.root, self.prefix, self.limit = root, prefix, limit
        self.parts, self.stream = [], None
        self.total, self.total_hash = 0, hashlib.sha256()

    def write(self, data):
        view, written = memoryview(data), len(data)
        while view:
            if self.stream is None:
                relative = f"{self.prefix}.part{len(self.parts) + 1:04d}"
                path = safe_path(self.root, relative)
                path.parent.mkdir(parents=True, exist_ok=True)
                self.stream, self.part_hash, self.part_size = path.open("xb"), hashlib.sha256(), 0
                self.parts.append({"path": relative})
            count = min(len(view), self.limit - self.part_size)
            chunk, view = view[:count], view[count:]
            self.stream.write(chunk)
            self.part_hash.update(chunk)
            self.total_hash.update(chunk)
            self.part_size += count
            self.total += count
            if self.part_size == self.limit:
                self.finish_part()
        return written

    def flush(self):
        if self.stream:
            self.stream.flush()

    def finish_part(self):
        if self.stream:
            self.stream.close()
            self.parts[-1].update(bytes=self.part_size, sha256=self.part_hash.hexdigest())
            self.stream = None


def store_file(source, target_root, relative, threshold, part_bytes):
    original_hash, size = hashlib.sha256(), 0
    if source.stat().st_size > threshold:
        sink = PartWriter(target_root, relative + ".gz", part_bytes)
        with source.open("rb") as stream, gzip.GzipFile(filename="", mode="wb", fileobj=sink, mtime=0, compresslevel=6) as output:
            for chunk in iter(lambda: stream.read(BLOCK_BYTES), b""):
                original_hash.update(chunk)
                size += len(chunk)
                output.write(chunk)
        sink.finish_part()
        encoding, stored = "gzip", {"bytes": sink.total, "sha256": sink.total_hash.hexdigest(), "parts": sink.parts}
    else:
        target = safe_path(target_root, relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        with source.open("rb") as stream, target.open("xb") as output:
            for chunk in iter(lambda: stream.read(BLOCK_BYTES), b""):
                original_hash.update(chunk)
                size += len(chunk)
                output.write(chunk)
        encoding = "identity"
        stored = {"bytes": size, "sha256": original_hash.hexdigest(), "parts": [{"path": relative, "bytes": size, "sha256": original_hash.hexdigest()}]}
    return {"path": relative, "encoding": encoding, "uncompressed": {"bytes": size, "sha256": original_hash.hexdigest()}, "stored": stored}


class PartReader(io.RawIOBase):
    def __init__(self, paths):
        self.paths, self.current = iter(paths), None

    def readable(self):
        return True

    def readinto(self, buffer):
        while True:
            if self.current is None:
                path = next(self.paths, None)
                if path is None:
                    return 0
                self.current = path.open("rb")
            count = self.current.readinto(buffer)
            if count:
                return count
            self.current.close()
            self.current = None

    def close(self):
        if self.current:
            self.current.close()
        super().close()


def restore_payload(archive, destination, manifest):
    if manifest.get("schema") != SCHEMA or manifest.get("status") != "complete":
        raise ValueError("Complete native archive manifest required")
    paths = set()
    for entry in manifest["files"]:
        if entry["path"] in paths:
            raise ValueError("Duplicate restored path")
        paths.add(entry["path"])
        target = safe_path(destination, entry["path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        total_hash, total_size, parts = hashlib.sha256(), 0, []
        for part in entry["stored"]["parts"]:
            source = safe_path(archive, part["path"])
            hasher, size = hashlib.sha256(), 0
            with source.open("rb") as stream:
                for chunk in iter(lambda: stream.read(BLOCK_BYTES), b""):
                    hasher.update(chunk)
                    total_hash.update(chunk)
                    size += len(chunk)
                    total_size += len(chunk)
            if size > GIT_SAFE_BYTES or size != part["bytes"] or hasher.hexdigest() != part["sha256"]:
                raise ValueError("Stored part size/hash mismatch or oversized Git object")
            parts.append(source)
        if total_size != entry["stored"]["bytes"] or total_hash.hexdigest() != entry["stored"]["sha256"]:
            raise ValueError("Stored stream size/hash mismatch")
        raw_hash, size = hashlib.sha256(), 0
        with io.BufferedReader(PartReader(parts)) as concatenated, target.open("xb") as output:
            if entry["encoding"] == "gzip":
                stream = gzip.GzipFile(fileobj=concatenated, mode="rb")
            elif entry["encoding"] == "identity":
                stream = concatenated
            else:
                raise ValueError("Unknown archive encoding")
            try:
                for chunk in iter(lambda: stream.read(BLOCK_BYTES), b""):
                    raw_hash.update(chunk)
                    size += len(chunk)
                    output.write(chunk)
            finally:
                if stream is not concatenated:
                    stream.close()
        if size != entry["uncompressed"]["bytes"] or raw_hash.hexdigest() != entry["uncompressed"]["sha256"]:
            raise ValueError("Restored uncompressed bytes/hash mismatch")
    identity = completed_receipts(destination / "selection", destination / "confirmation")
    refs = verify_raw_references({role: destination / role for role in ("selection", "confirmation")})
    if identity != manifest["completedReceipts"] or refs != manifest["rawEvidence"]:
        raise ValueError("Restored completion/rawEvidence identities differ")
    return {"files": len(paths), "rawEvidenceSlicesVerified": refs["uniqueSlicesVerified"]}


def archive_run(selection, confirmation, destination, threshold=GIT_SAFE_BYTES, part_bytes=PART_BYTES):
    roots = {"selection": Path(selection).resolve(), "confirmation": Path(confirmation).resolve()}
    destination = Path(destination).resolve()
    if destination.exists() or not 0 < threshold <= GIT_SAFE_BYTES or not 0 < part_bytes <= PART_BYTES:
        raise ValueError("Use a new archive path and Git-safe size limits")
    for root in roots.values():
        if destination == root or root in destination.parents:
            raise ValueError("Archive output must be outside input directories")
    identity = completed_receipts(roots["selection"], roots["confirmation"])
    references = verify_raw_references(roots)
    sources = [(role, path) for role, root in roots.items() for path in files_in(root)]
    before = {path: fingerprint(path) for _, path in sources}
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".native-archive-", dir=destination.parent) as temporary:
        payload = Path(temporary) / "archive"
        payload.mkdir()
        files = [store_file(path, payload, f"{role}/{path.relative_to(roots[role]).as_posix()}", threshold, part_bytes) for role, path in sources]
        current = [(role, path) for role, root in roots.items() for path in files_in(root)]
        if current != sources or any(fingerprint(path) != before[path] for _, path in sources):
            raise ValueError("Source outputs changed during collection; archive a completed stable run")
        manifest = {"schema": SCHEMA, "status": "complete", "sources": {role: str(root) for role, root in roots.items()},
                    "compressionThresholdBytes": threshold, "maximumPartBytes": part_bytes, "gzip": {"mtime": 0, "level": 6, "filename": "", "zlibRuntimeVersion": zlib.ZLIB_RUNTIME_VERSION},
                    "archiverSha256": digest(Path(__file__).read_bytes()),
                    "completedReceipts": identity, "rawEvidence": references, "files": files,
                    "restoration": "Concatenate each entry's stored.parts in listed order; gzip-decompress if encoding=gzip, otherwise copy. Uncompressed offsets refer to restored journal bytes.",
                    "hiddenOracleInputsRead": False, "modelOrGpuCalls": False}
        # Validate the archive itself, including offsets after decompression,
        # before it becomes the requested destination.
        restored = Path(temporary) / "verified"
        restored.mkdir()
        restore_payload(payload, restored, manifest)
        data = (json.dumps(manifest, indent=2) + "\n").encode()
        if len(data) > GIT_SAFE_BYTES:
            raise ValueError("Archive manifest itself exceeds Git-safe size")
        (payload / "archive-manifest.json").write_bytes(data)
        (payload / "archive-manifest.sha256").write_text(digest(data) + "  archive-manifest.json\n")
        if destination.exists():
            raise ValueError("Archive destination appeared during collection")
        payload.rename(destination)
    return manifest


def restore_archive(archive, destination=None):
    archive = Path(archive).resolve()
    data = (archive / "archive-manifest.json").read_bytes()
    expected = (archive / "archive-manifest.sha256").read_text().split()[0]
    if digest(data) != expected:
        raise ValueError("Archive manifest checksum mismatch")
    manifest = json.loads(data)
    destination = Path(destination).resolve() if destination else None
    if destination and destination.exists():
        raise ValueError("Restore output must be a new directory")
    if destination and (destination == archive or archive in destination.parents):
        raise ValueError("Restore outside the archive to avoid adding raw large files to its Git-safe package")
    parent = destination.parent if destination else None
    if parent:
        parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".native-restore-", dir=parent) as temporary:
        payload = Path(temporary) / "restored"
        payload.mkdir()
        result = restore_payload(archive, payload, manifest)
        if destination:
            payload.rename(destination)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="action", required=True)
    create = sub.add_parser("archive")
    create.add_argument("--selection-dir", required=True)
    create.add_argument("--confirmation-dir", required=True)
    create.add_argument("--output", required=True)
    for command in ("restore", "verify"):
        p = sub.add_parser(command)
        p.add_argument("--archive", required=True)
        if command == "restore":
            p.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.action == "archive":
        manifest = archive_run(args.selection_dir, args.confirmation_dir, args.output)
        print(json.dumps({"status": "archived_verified", "files": len(manifest["files"]), "uncompressedBytes": sum(f["uncompressed"]["bytes"] for f in manifest["files"]), "storedBytes": sum(f["stored"]["bytes"] for f in manifest["files"]), "output": args.output}))
    else:
        print(json.dumps({"status": "restored_verified" if args.action == "restore" else "archive_verified", **restore_archive(args.archive, getattr(args, "output", None))}))


if __name__ == "__main__":
    main()
