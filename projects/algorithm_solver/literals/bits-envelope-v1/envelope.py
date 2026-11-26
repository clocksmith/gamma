"""TotalByteEnvelope: every byte a BITS reader needs, measured from the artifacts.

    python3 -B envelope.py [GAMMA_CHECKOUT]           reconcile the four frozen matched80 packages
    python3 -B envelope.py --bundle DIR CLAIM.json    check one bundle against a byte claim

Standard library only. It imports nothing from Gamma (no model.py, no codec, no other
checker) and never trusts a producer's byte count: sizes come from the artifact files.

An envelope has six components, each measured:

    payload     packet bytes after the fixed header (the packed 6-bit / escape codes)
    framing     the fixed packet header: magic, the 32-byte dictionary hash, the uint32 code count
    dictionary  the whole LTD1 file (magic, count, length prefixes, entry bytes)
    index       bytes a reader needs to find record i inside one stored blob
    decoder     a decoder charge, counted only when the claim says it is part of the package
    total       the sum of the five

plus `ordered_vocab_sha256`, the SHA-256 of the LTD1 bytes, which fixes the slot order.

A claim passes only when every component, the total and the ordered vocabulary hash match
the measurement exactly: drift must be 0 B. The checker fails closed:

- a claim that leaves out `index`, or sets it below the measured index, is rejected as an
  uncounted index;
- a claim whose vocabulary, in slot order, is not the stored dictionary is rejected, even
  when the same entries appear in another order (the slot-swap case of Gamma 06562147d);
- a packet whose embedded dictionary hash is not the stored dictionary's is rejected;
- a bundle file that no role names is rejected; it is not a free byte;
- the frozen matched80 packages store one file per program and no index, so their
  `package_bytes` reconcile as payload + framing + dictionary (+ decoder) and are reported as
  `random_access_total: null`. They are never promoted to a random-access total.
"""
import hashlib
import json
import os
import subprocess
import sys

PIN = "59ff04415ff2afd04ff2ed451340f4f02852bf18"
ROOT = "projects/algorithm_solver/literals/sixbit-v1"
JOBS = {  # job: (run folder, escape arm)
    "b-w-compact": ("run-v1", False),
    "b-u-compact": ("run-jupiter-v1", False),
    "c-w-compact": ("run-v1", True),
    "c-u-compact": ("run-v1", True),
}
COMPONENTS = ("payload", "framing", "dictionary", "index", "decoder")
HEADER = {False: b"LTV1\x06", True: b"LTE6"}


class Reject(ValueError):
    pass


def require(test, reason):
    if not test:
        raise Reject(reason)


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def strict_json(data):
    def pairs(items):
        result = dict(items)
        require(len(result) == len(items), "duplicate JSON key")
        return result
    return json.loads(data, object_pairs_hook=pairs)


def u32be(data):
    require(len(data) == 4, "truncated uint32")
    return int.from_bytes(data, "big")


def ltd1_entries(data):
    """Parse an LTD1 dictionary: magic, uint32 count, then (uint32 length, UTF-8 bytes) per slot."""
    require(data[:4] == b"LTD1", "dictionary magic is not LTD1")
    count = u32be(data[4:8])
    cursor, entries = 8, []
    for _ in range(count):
        size = u32be(data[cursor:cursor + 4])
        cursor += 4
        entry = data[cursor:cursor + size]
        require(size > 0 and len(entry) == size, "bad dictionary entry length")
        entries.append(entry.decode("utf-8"))
        cursor += size
    require(cursor == len(data), "trailing bytes after the dictionary")
    require(len(set(entries)) == count, "duplicate dictionary entry")
    return entries


def ltd1_bytes(entries):
    """Encode a slot-ordered vocabulary as LTD1. Its SHA-256 is the ordered vocabulary hash."""
    out = [b"LTD1", len(entries).to_bytes(4, "big")]
    for entry in entries:
        raw = entry.encode("utf-8")
        out += [len(raw).to_bytes(4, "big"), raw]
    return b"".join(out)


def split_packet(packet, dictionary_hash, escape):
    """Return (framing, payload) byte counts of one packet; check what can be checked without decoding."""
    header = HEADER[escape]
    framing = len(header) + 32 + 4
    require(packet.startswith(header), "packet magic or width")
    require(packet[len(header):len(header) + 32] == bytes.fromhex(dictionary_hash),
            "packet names a different dictionary")
    codes = u32be(packet[len(header) + 32:framing])
    payload = len(packet) - framing
    if escape:  # 6 bits per code, 7 more per escape: between 6n and 13n bits, padded to a byte
        require(6 * codes <= 8 * payload <= 13 * codes + 7, "payload length impossible for its code count")
    else:
        require(payload == -(-6 * codes // 8), "payload length is not ceil(6n/8)")
    return framing, payload


def measure(dictionary, packets, escape, index=b"", decoder_bytes=0):
    dictionary_hash = sha(dictionary)
    ltd1_entries(dictionary)
    framing = payload = 0
    for packet in packets:
        f, p = split_packet(packet, dictionary_hash, escape)
        framing += f
        payload += p
    env = {"payload": payload, "framing": framing, "dictionary": len(dictionary),
           "index": len(index), "decoder": decoder_bytes}
    env["total"] = sum(env[c] for c in COMPONENTS)
    env["ordered_vocab_sha256"] = dictionary_hash
    return env


def check_claim(env, claim):
    """Accept only a claim equal to the measured envelope. Returns drift (0) or raises Reject."""
    require(isinstance(claim, dict), "claim is not an object")
    require("index" in claim and isinstance(claim["index"], int), "uncounted index: claim has no index component")
    require(claim["index"] >= env["index"],
            f"uncounted index: claim {claim['index']} B, measured {env['index']} B")
    vocab = claim.get("vocabulary")
    require(isinstance(vocab, list) and all(isinstance(v, str) for v in vocab), "claim has no slot-ordered vocabulary")
    require(sha(ltd1_bytes(vocab)) == env["ordered_vocab_sha256"],
            "ordered vocabulary differs from the stored dictionary (slot order or entries)")
    require(claim.get("ordered_vocab_sha256") == env["ordered_vocab_sha256"], "ordered vocabulary hash")
    for component in COMPONENTS:
        require(isinstance(claim.get(component), int), f"claim lacks {component}")
        require(claim[component] == env[component],
                f"{component}: claim {claim[component]} B, measured {env[component]} B")
    require(claim.get("total") == sum(claim[c] for c in COMPONENTS), "claimed components do not sum to the claimed total")
    drift = claim["total"] - env["total"]
    require(drift == 0, f"total drift {drift} B")
    return drift


# ------------------------------------------------------------------ bundle: one blob plus an index

def read_bundle(folder):
    """A bundle folder: bundle.json names each file's role; records are concatenated packets.

    bundle.json = {"records": n, "escape": bool, "decoder_bytes": int,
                   "files": {"<name>": "dictionary" | "records" | "index"}}
    The index is n + 1 big-endian uint32 offsets into the records file, from 0 to its length.
    """
    spec = strict_json(open(os.path.join(folder, "bundle.json"), "rb").read())
    files = spec["files"]
    present = sorted(n for n in os.listdir(folder) if n != "bundle.json")
    require(sorted(files) == present, f"bundle files and roles differ: {sorted(set(present) ^ set(files))}")
    roles = sorted(files.values())
    require(roles == ["dictionary", "index", "records"], "bundle needs exactly one dictionary, records and index")
    by_role = {role: open(os.path.join(folder, name), "rb").read() for name, role in files.items()}
    n, blob, index = spec["records"], by_role["records"], by_role["index"]
    require(isinstance(n, int) and n > 0 and len(index) == 4 * (n + 1), "index length is not 4(n+1)")
    offsets = [u32be(index[4 * i:4 * i + 4]) for i in range(n + 1)]
    require(offsets[0] == 0 and offsets[-1] == len(blob) and all(a < b for a, b in zip(offsets, offsets[1:])),
            "index offsets are not the record boundaries")
    packets = [blob[a:b] for a, b in zip(offsets, offsets[1:])]
    return measure(by_role["dictionary"], packets, spec["escape"], index, spec.get("decoder_bytes", 0))


# ------------------------------------------------------------------ the frozen matched80 packages

class PinnedBlobs:
    """Read blobs at PIN through one `git cat-file --batch` process."""

    def __init__(self, checkout):
        self.proc = subprocess.Popen(["git", "--no-replace-objects", "-C", checkout, "cat-file", "--batch"],
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    def __call__(self, path):
        self.proc.stdin.write(f"{PIN}:{path}\n".encode())
        self.proc.stdin.flush()
        head = self.proc.stdout.readline().split()
        require(len(head) == 3 and head[1] == b"blob", f"not a blob at the pin: {path}")
        data = self.proc.stdout.read(int(head[2]))
        self.proc.stdout.read(1)
        return data

    def close(self):
        self.proc.stdin.close()
        self.proc.wait()


def frozen_rows(checkout):
    git_blob = PinnedBlobs(checkout)
    try:
        return _frozen_rows(lambda _checkout, path: git_blob(path), checkout)
    finally:
        git_blob.close()


def _frozen_rows(git_blob, checkout):
    rows = []
    for job, (run, escape) in JOBS.items():
        base = f"{ROOT}/{run}/{job}"
        m = strict_json(git_blob(checkout, f"{base}/manifest.json"))
        package = m if escape else m["package"]
        dictionary = git_blob(checkout, f"{base}/dictionary.ltd")
        extension = ".lte" if escape else ".ltv"
        packets = [git_blob(checkout, f"{base}/packets/{pid}{extension}") for pid in package["programs"]]
        decoder = m["decoder_bytes"] if escape else 0
        env = measure(dictionary, packets, escape, b"", decoder)
        require(ltd1_entries(dictionary) == m["vocabulary"], f"{job}: manifest vocabulary is not the dictionary's slot order")
        require(package["dictionary_sha256"] == env["ordered_vocab_sha256"], f"{job}: dictionary hash")
        require(package["dictionary_bytes"] == env["dictionary"], f"{job}: dictionary bytes")
        require(package["packet_bytes"] == env["payload"] + env["framing"], f"{job}: packet bytes")
        drift = package["package_bytes"] - env["total"]
        require(drift == 0, f"{job}: package_bytes drift {drift} B")
        rows.append({"job": job, "records": len(packets), **env, "package_bytes_drift": drift,
                     "index_stored": False, "random_access_total": None,
                     "note": "one file per program and no index: package_bytes is not a random-access total"})
    return rows


def emit_artifacts(checkout, job, out):
    """Write one frozen package as a split random-access artifact set for short-record-byte-accounting-v1.

    Files: dictionary.ltd; framing.bin, the fixed packet headers back to back (a reader finds header i at
    i x header size); payload.bin, the code streams back to back; index.bin, n + 1 little-endian uint32
    offsets (starts and end) into payload.bin; for the escape arm, the decoder source the package charges
    for, as `model`. Also writes OUT.report.json, this checker's envelope in the accountant's vocabulary.
    """
    run, escape = JOBS[job]
    base = f"{ROOT}/{run}/{job}"
    git_blob = PinnedBlobs(checkout)
    try:
        m = strict_json(git_blob(f"{base}/manifest.json"))
        package = m if escape else m["package"]
        dictionary = git_blob(f"{base}/dictionary.ltd")
        extension = ".lte" if escape else ".ltv"
        packets = [git_blob(f"{base}/packets/{pid}{extension}") for pid in package["programs"]]
        decoder = git_blob(f"{ROOT}/escape6_decoder.py") if escape else b""
    finally:
        git_blob.close()
    require(len(decoder) == (m["decoder_bytes"] if escape else 0), "decoder file is not the charged decoder size")
    head = len(HEADER[escape]) + 32 + 4
    starts, payloads = [0], []
    for packet in packets:
        split_packet(packet, sha(dictionary), escape)
        payloads.append(packet[head:])
        starts.append(starts[-1] + len(payloads[-1]))
    index = b"".join(o.to_bytes(4, "little") for o in starts)
    env = measure(dictionary, packets, escape, index, len(decoder))
    os.makedirs(out)
    files = {"dictionary.ltd": dictionary, "framing.bin": b"".join(p[:head] for p in packets),
             "payload.bin": b"".join(payloads), "index.bin": index}
    roles = [{"path": "dictionary.ltd", "role": "dictionary"}, {"path": "framing.bin", "role": "framing"},
             {"path": "payload.bin", "role": "payload"},
             {"path": "index.bin", "role": "index", "offset_width": 4, "offsets": "starts+end", "into": "payload.bin"}]
    if escape:
        files["decoder.py"] = decoder
        roles.append({"path": "decoder.py", "role": "model"})
    for name, data in files.items():
        with open(os.path.join(out, name), "wb") as handle:
            handle.write(data)
    with open(os.path.join(out, "artifacts.json"), "w") as handle:
        json.dump({"format": "bits-split-v1", "records": len(packets), "files": roles}, handle, indent=1)
    report = {"records": len(packets), "header": 0, "dictionary": env["dictionary"], "model": env["decoder"],
              "index": env["index"], "framing": env["framing"], "payload": env["payload"], "total": env["total"]}
    with open(out.rstrip(os.sep) + ".report.json", "w") as handle:
        json.dump(report, handle, indent=1)
    return env


def main(argv):
    try:
        if argv[:1] == ["--emit-artifacts"]:
            require(len(argv) in (3, 4), "usage: envelope.py --emit-artifacts JOB OUTDIR [GAMMA_CHECKOUT]")
            require(argv[1] in JOBS, f"unknown job; one of {', '.join(JOBS)}")
            env = emit_artifacts(argv[3] if len(argv) == 4 else ".", argv[1], argv[2])
            print(json.dumps({"job": argv[1], "envelope": env}, indent=2))
            return 0
        if argv[:1] == ["--bundle"]:
            require(len(argv) == 3, "usage: envelope.py --bundle DIR CLAIM.json")
            env = read_bundle(argv[1])
            drift = check_claim(env, strict_json(open(argv[2], "rb").read()))
            print(json.dumps({"envelope": env, "drift": drift, "random_access_total": env["total"]}, indent=2))
            return 0
        checkout = argv[0] if argv else "."
        print(json.dumps({"pin": PIN, "packages": frozen_rows(checkout)}, indent=2))
        return 0
    except (Reject, KeyError, TypeError, ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f"REJECT: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
