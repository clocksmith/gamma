"""Independent, solver-free checker for the pinned matched80 compact jobs."""
import argparse
from collections import defaultdict
import hashlib
import json
import subprocess
import sys

PIN = "59ff04415ff2afd04ff2ed451340f4f02852bf18"
ROOT = "projects/algorithm_solver/literals"
JOBS = {f"{k.lower()}-{r.lower()}-compact": ("run-jupiter-v1" if (k, r) == ("B", "U")
        else "run-v1", k, r) for k in "ABC" for r in "WU"}


class Invalid(ValueError):
    pass


def require(test, reason):
    if not test:
        raise Invalid(reason)


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def integer(n):
    return type(n) is int


def json_read(data):
    def object_pairs(pairs):
        result = dict(pairs)
        require(len(result) == len(pairs), "duplicate JSON key")
        return result
    return json.loads(data, object_pairs_hook=object_pairs)


class Frozen:
    def __init__(self, checkout):
        self.checkout = checkout

    def git(self, *args):
        return subprocess.check_output(["git", "--no-replace-objects", "-C", self.checkout, *args])

    def __call__(self, path):
        return self.git("cat-file", "blob", f"{PIN}:{ROOT}/{path}")

    def size(self, path):
        return int(self.git("cat-file", "-s", f"{PIN}:{ROOT}/{path}"))

    def packet_ids(self, job_path, extension):
        base = f"{ROOT}/{job_path}/packets/"
        paths = self.git("ls-tree", "-r", "--name-only", "-z", PIN, "--", base)
        result = set()
        for path in paths.decode().split("\0")[:-1]:
            name = path.removeprefix(base)
            require(name.endswith(extension) and name.removesuffix(extension).isdecimal(),
                    "unexpected packet file")
            result.add(name.removesuffix(extension))
        return result


def compact_sources(read, trusted_read=None):
    # Separate trust anchor also lets tests exercise manifest rehashing without altering Git.
    trusted_read = trusted_read or read
    ids = json_read(trusted_read("matched80-v1/labels/ids.json"))
    require(len(ids) == len(set(ids)) == 80 and all(map(integer, ids)), "wrong cohort IDs")
    source_manifest = "scale-v2/generated/manifest.json"
    receipts = ["scale-v2/qualification/report.json", "scale-v2/qualification-rerun-v1/report.json"]

    def compact_rows(path, reader):
        rows = [r for r in json_read(reader(path))["rows"] if r["variant"] == "compact"]
        result = {r["id"]: r for r in rows}
        require(len(rows) == len(result) and set(result) == set(ids), "wrong compact population")
        return result

    rows = compact_rows(source_manifest, read)
    trusted = compact_rows(source_manifest, trusted_read)
    quals = [compact_rows(p, read) for p in receipts]
    result = {}
    for pid in ids:
        row = rows[pid]
        path = f"sources/{pid:04d}-compact.js"
        raw = read("scale-v2/generated/" + path)
        require(row["file"] == path == trusted[pid]["file"]
                and digest(raw) == row["sha256"] == trusted[pid]["sha256"],
                f"frozen source identity: {pid}")
        for receipt in quals:
            q = receipt[pid]
            require(q["file"] == path and q["sha256"] == digest(raw)
                    and q["passed"] is True and q["checks_passed"] == q["checks_total"]
                    and q["checks_total"] > 0, f"qualification mismatch: {pid}")
        result[str(pid)] = raw.decode("utf-8")
    return result


class Language:
    def __init__(self, programs):
        self.programs = programs
        self.whole = set(programs.values())
        self.alphabet = set().union(*map(set, self.whole))
        first = {}
        self.shared = set()
        for pid, source in programs.items():
            for i in range(len(source)):
                size = len(source[i].encode())
                for j in range(i + 2, min(i + 161, len(source) + 1)):
                    size += len(source[j - 1].encode())
                    if size > 160:
                        break
                    piece = source[i:j]
                    if first.setdefault(piece, pid) != pid:
                        self.shared.add(piece)
        self.shared.difference_update(self.whole)

    def allows(self, rule, piece):
        if not piece or piece in self.whole:
            return False
        if rule == "W":
            return piece in self.alphabet or piece in self.shared
        return any(piece in source for source in self.whole)


def lower(language, kind, rule, cert, budget):
    scale, mu, potentials = cert["scale"], cert["mu"], cert["potentials"]
    require(cert["kind"] == ("B1" if kind == "B" else kind), "wrong certificate objective")
    require(integer(scale) and scale > 0 and integer(mu) and mu >= 0
            and (kind != "A" or mu == 0), "invalid certificate scale/multiplier")
    require(set(potentials) == set(language.programs), "wrong potential cohort")
    total = -mu * budget
    rebates = defaultdict(int)
    literal_cost = 7 * scale if kind == "C" else 0
    for pid, source in language.programs.items():
        p = potentials[pid]
        require(isinstance(p, list) and len(p) == len(source) + 1 and all(map(integer, p)),
                f"invalid potential vector: {pid}")
        delta = p[0] - p[-1]
        total += delta
        if kind == "B":
            total += min(0, scale - delta)  # omitted program
        for i, char in enumerate(source):
            if kind == "C" and escape_ascii(ord(char)):
                total += min(0, 15 * scale - (p[i] - p[i + 1]))
            limit = len(source) if rule == "U" else min(len(source), i + 160)
            cutoff = p[i] - literal_cost
            for j in range(i + 1, limit + 1):
                if p[j] >= cutoff:
                    continue  # nonnegative reduced costs cannot contribute
                piece = source[i:j]
                if rule == "W":
                    if piece not in language.shared and not (j == i + 1 and piece in language.alphabet
                                                              and piece not in language.whole):
                        continue
                elif piece in language.whole:
                    continue
                rebates[piece] += cutoff - p[j]
    entry_price = scale if kind == "A" else mu
    total += sum(min(0, entry_price - rebate) for rebate in rebates.values())
    return total, scale


def escape_ascii(code):
    return code == 10 or 32 <= code <= 126


def u32(data):
    require(len(data) == 4, "truncated uint32")
    return int.from_bytes(data, "big")


def dictionary(data):
    require(data[:4] == b"LTD1", "wrong dictionary magic")
    count = u32(data[4:8])
    require(count <= (len(data) - 8) // 5, "truncated dictionary")
    entries = []
    cursor = 8
    for _ in range(count):
        size = u32(data[cursor:cursor + 4])
        cursor += 4
        entry = data[cursor:cursor + size]
        require(size > 0 and len(entry) == size, "bad dictionary entry length")
        entries.append(entry.decode("utf-8"))
        cursor += size
    require(cursor == len(data) and len(set(entries)) == count, "duplicate or trailing dictionary data")
    return entries


def decode(packet, entries, dict_hash, escape):
    header = b"LTE6" if escape else b"LTV1\x06"
    start = len(header)
    require(packet.startswith(header) and packet[start:start + 32] == bytes.fromhex(dict_hash),
            "bad packet magic, width, or dictionary hash")
    count = u32(packet[start + 32:start + 36])
    payload = packet[start + 36:]
    bit_count = len(payload) * 8
    require(6 * count <= bit_count, "truncated packet payload")
    packed = int.from_bytes(payload, "big")
    left = bit_count

    def take(width):
        nonlocal left
        left -= width
        require(left >= 0, "truncated packet token")
        return (packed >> left) & ((1 << width) - 1)

    chunks, escapes = [], 0
    for _ in range(count):
        code = take(6)
        if escape and code == 63:
            raw = take(7)
            require(escape_ascii(raw), "invalid escaped ASCII")
            chunks.append(bytes((raw,)))
            escapes += 1
        else:
            require(code < len(entries), "unused dictionary code")
            chunks.append(entries[code].encode())
    require(left < 8 and packed & ((1 << left) - 1) == 0, "noncanonical packet end")
    return b"".join(chunks), count - escapes, escapes


def segmentation(source, entries):
    """Return a list of pieces constituting an exact cover, if one exists."""
    parent = {0: None}
    for i in range(len(source)):
        if i in parent:
            for piece in entries:
                if source.startswith(piece, i):
                    parent.setdefault(i + len(piece), (i, piece))
    if len(source) not in parent:
        return None
    path = []
    i = len(source)
    while i:
        i, piece = parent[i]
        path.append(piece)
    return list(reversed(path))


def row_objectives(kind, cohort, numer, scale, entries, covered, presses, claim):
    rounded = -(-numer // scale)
    if kind == "A":
        bound, feasible, field = rounded, entries, "min_entries_at_least"
    elif kind == "B":
        bound, feasible, field = cohort - rounded, covered, "coverage_at_most"
    else:
        bound, feasible, field = rounded, presses, "presses_at_least"
    require(integer(claim[field]) and claim[field] == bound, "claimed integer bound not recomputed")
    require(feasible <= bound if kind == "B" else bound <= feasible, "bound contradicts witness")
    return {"bound": bound, "witness": feasible, "tight": bound == feasible,
            "exact_rational_lower": [numer, scale], "relaxed_objective": "omissions" if kind == "B" else "same",
            "objective": {"A": "entries", "B": "coverage", "C": "frozen presses"}[kind]}


def check_job(read, language, job, claim, check_inventory=None, decoder_size=None):
    run, kind, rule = JOBS[job]
    base = f"sixbit-v1/{run}/{job}"
    m = json_read(read(f"{base}/manifest.json"))
    cert = json_read(read(f"{base}/certificate.json"))
    cohort = language.programs
    require((m["job"], m["experiment"], m["rule"], m["style"]) == (job, kind, rule, "compact"),
            "job manifest binding")
    slots = m["vocabulary"]
    require(isinstance(slots, list) and all(isinstance(x, str) for x in slots)
            and len(set(slots)) == len(slots) == m["entries"], "invalid vocabulary")
    require(all(language.allows(rule, piece) for piece in slots), "ineligible dictionary entry")
    selected = escaped = presses = 0
    budget = {"A": 0, "B": 64, "C": 63}[kind]
    if kind == "A":
        require(all(segmentation(source, slots) is not None for source in cohort.values()),
                "A witness does not segment entire cohort")
        covered = len(cohort)
    else:
        escape = kind == "C"
        package = m if escape else m["package"]
        extension = ".lte" if escape else ".ltv"
        raw = read(f"{base}/dictionary.ltd")
        hash_hex = digest(raw)
        require(dictionary(raw) == slots, "dictionary order does not match manifest slots")
        require(len(slots) <= budget and package["dictionary_bytes"] == len(raw)
                and package["dictionary_sha256"] == hash_hex, "dictionary budget or identity")
        if not escape:
            require(package["six_bit_packets"] is True and package["entries"] == slots,
                    "B package slots do not match")
        programs = package["programs"]
        ids = set(programs)
        if escape:
            require(ids == set(cohort), "C packet population")
        else:
            require(m["covered_programs"] == [i for i in cohort if i in ids]
                    and m["uncovered_programs"] == [i for i in cohort if i not in ids]
                    and ids <= set(cohort), "B packet population")
        if check_inventory is not None:
            require(ids == check_inventory(base, extension), "packet inventory differs from manifest")
        packet_bytes = 0
        for pid in cohort:
            if pid not in ids:
                continue
            packet = read(f"{base}/packets/{pid}{extension}")
            row = programs[pid]
            expected = cohort[pid].encode()
            require(row["packet_sha256"] == digest(packet) and row["packet_bytes"] == len(packet)
                    and row["source_sha256"] == digest(expected), f"packet metadata: {pid}")
            result, ns, ne = decode(packet, slots, hash_hex, escape)
            require(result == expected, f"decoded bytes differ for {pid}")
            require(row["selections"] == ns, f"selection recount differs: {pid}")
            if escape:
                require((row["escapes"], row["tokens"], row["presses"]) == (ne, ns + ne, 7 * ns + 15 * ne),
                        f"ESC recount differs: {pid}")
            else:
                require(m["selections"][pid] == ns, f"B selection split: {pid}")
            selected += ns
            escaped += ne
            packet_bytes += len(packet)
        covered = len(ids)
        presses = 7 * selected + 15 * escaped
        require(m["presses"] == presses and package["packet_bytes"] == packet_bytes,
                "packet aggregate mismatch")
        subtotal = packet_bytes + len(raw)
        if escape:
            require((m["selections"], m["escapes"], m["package_bytes_without_decoder"])
                    == (selected, escaped, subtotal), "escape aggregate mismatch")
            if decoder_size is not None:
                require(m["decoder_bytes"] == decoder_size, "historical decoder byte charge")
            subtotal += m["decoder_bytes"]
        require(package["package_bytes"] == subtotal, "package size mismatch")
    require(m["covered"] == covered, "covered count mismatch")
    numer, scale = lower(language, kind, rule, cert, budget)
    result = row_objectives(kind, len(cohort), numer, scale, len(slots), covered, presses, claim)
    return result | {"job": job, "run": run, "cohort": len(cohort), "covered": covered,
                     "entries": len(slots), **({"selections": selected, "escapes": escaped,
                      "frozen_presses": presses} if kind != "A" else {})}


def claims(read):
    result = {}
    for job, (run, _, _) in JOBS.items():
        rows = json_read(read(f"sixbit-v1/{run}/verification.json"))
        matches = [row for row in rows if row["job"] == job]
        require(len(matches) == 1, f"missing or duplicate claim: {job}")
        result[job] = matches[0]
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", nargs="?", default=".")
    args = parser.parse_args(argv)
    data = Frozen(args.checkout)
    try:
        language = Language(compact_sources(data))
        stored = claims(data)
        size = data.size("sixbit-v1/escape6_decoder.py")  # stat only, never read or run it
        rows = [check_job(data, language, job, stored[job], data.packet_ids, size) for job in JOBS]
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as exc:
        print(f"REJECT: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"pin": PIN, "results": rows}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
