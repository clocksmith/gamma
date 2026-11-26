#!/usr/bin/env python3
"""Independent decoder and checker for BOH1 archives.

Written by the scorer from FORMAT.md alone. It imports nothing from this folder
and uses the Python standard library only.

For one set it decodes every archive in <out>/archives/<set>/, and for each:

  * checks that every decoded file equals its source file byte for byte
    (source files and their order come from the set manifest);
  * checks that the archive begins with exactly the bytes of
    <frozen>/<name>.boh;
  * counts, from the bit stream itself, the files, the tokens (an escape plus
    its byte is one token; end-of-file codes are not tokens) and the escapes.

It writes <out>/decode-<set>.json, then compares its counts with
<out>/results-<set>.json:

  archive size  ==  headers[name].bytes.complete
  tokens        ==  headers[name].bit_parse_tokens
  escapes       ==  headers[name].escapes_in_bit_parse
  entry count   ==  headers[name].entries

Any mismatch is a failure and the exit status is 1.

Usage:
  python3 -I independent_decode.py --set sets/fresh.json --root . --out out
"""

import argparse
import hashlib
import json
import os
import sys

MAGIC = b"BOH1"


class FormatError(Exception):
    pass


def read_varint(buf, pos):
    """Unsigned integer, seven bits at a time, least significant group first.
    Every byte except the last has its top bit set."""
    value = 0
    shift = 0
    while True:
        if pos >= len(buf):
            raise FormatError("varint runs past the end of the archive")
        b = buf[pos]
        pos += 1
        value |= (b & 0x7F) << shift
        shift += 7
        if not b & 0x80:
            return value, pos


def canonical_codes(lengths):
    """Code strings ('0'/'1') per symbol.

    Sort the symbols by code length, then by symbol number. The first gets the
    all-zero code of its length. Each later symbol gets the previous code plus
    one, shifted left by the difference in length."""
    order = sorted(range(len(lengths)), key=lambda s: (lengths[s], s))
    codes = [None] * len(lengths)
    code = 0
    prev_len = lengths[order[0]]
    codes[order[0]] = "0" * prev_len
    for s in order[1:]:
        length = lengths[s]
        code = (code + 1) << (length - prev_len)
        prev_len = length
        if code >> length:
            raise FormatError("code lengths do not form a prefix code")
        codes[s] = format(code, "b").zfill(length)
    return codes


def decode_archive(buf):
    """Decode one archive. Returns a dict with the decoded files and counts."""
    if buf[:4] != MAGIC:
        raise FormatError("bad magic")
    pos = 4
    n, pos = read_varint(buf, pos)
    entries = []
    for _ in range(n):
        if pos >= len(buf):
            raise FormatError("dictionary runs past the end of the archive")
        length = buf[pos]
        pos += 1
        if not 1 <= length <= 16:
            raise FormatError("entry length %d is outside 1..16" % length)
        if pos + length > len(buf):
            raise FormatError("dictionary runs past the end of the archive")
        entries.append(bytes(buf[pos:pos + length]))
        pos += length
    if pos + n + 2 > len(buf):
        raise FormatError("code table runs past the end of the archive")
    lengths = list(buf[pos:pos + n + 2])
    pos += n + 2
    for length in lengths:
        if not 1 <= length <= 255:
            raise FormatError("code length %d is outside 1..255" % length)
    header_bytes = pos
    f, pos = read_varint(buf, pos)
    payload_offset = pos

    codes = canonical_codes(lengths)
    table = {}
    for symbol, code in enumerate(codes):
        if code in table:
            raise FormatError("two symbols share a code")
        table[code] = symbol
    distinct_lengths = sorted(set(lengths))
    escape = n
    end_of_file = n + 1

    payload = buf[payload_offset:]
    if payload:
        bits = bin(int.from_bytes(payload, "big"))[2:].zfill(8 * len(payload))
    else:
        bits = ""
    total_bits = len(bits)

    files = []
    current = bytearray()
    tokens = 0
    escapes = 0
    bit = 0
    get = table.get
    while len(files) < f:
        symbol = None
        for length in distinct_lengths:
            if bit + length > total_bits:
                break
            symbol = get(bits[bit:bit + length])
            if symbol is not None:
                bit += length
                break
        if symbol is None:
            raise FormatError(
                "no code matches at payload bit %d (file %d)" % (bit, len(files)))
        if symbol < n:
            current += entries[symbol]
            tokens += 1
        elif symbol == escape:
            if bit + 8 > total_bits:
                raise FormatError("escaped byte runs past the end of the archive")
            current.append(int(bits[bit:bit + 8], 2))
            bit += 8
            tokens += 1
            escapes += 1
        else:
            assert symbol == end_of_file
            files.append(bytes(current))
            current = bytearray()

    trailing = bits[bit:]
    return {
        "entries": n,
        "files": files,
        "file_count": f,
        "tokens": tokens,
        "escapes": escapes,
        "header_bytes": header_bytes,
        "payload_offset": payload_offset,
        "payload_bytes": len(payload),
        "payload_bits_used": bit,
        "padding_bits": len(trailing),
        "padding_all_zero": "1" not in trailing,
    }


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--set", required=True, dest="set_path",
                    help="set manifest (JSON with 'set' and 'files')")
    ap.add_argument("--root", required=True,
                    help="directory the manifest paths are relative to")
    ap.add_argument("--out", required=True,
                    help="output directory of the frozen scoring command")
    ap.add_argument("--frozen", default="frozen",
                    help="directory holding the frozen headers <name>.boh")
    args = ap.parse_args()

    with open(args.set_path, "rb") as fh:
        manifest_bytes = fh.read()
    manifest = json.loads(manifest_bytes)
    set_name = manifest["set"]

    sources = []
    sources_match_manifest = True
    for item in manifest["files"]:
        with open(os.path.join(args.root, item["path"]), "rb") as fh:
            data = fh.read()
        sources.append(data)
        if "sha256" in item and sha256(data) != item["sha256"]:
            sources_match_manifest = False
        if "bytes" in item and len(data) != item["bytes"]:
            sources_match_manifest = False

    archive_dir = os.path.join(args.out, "archives", set_name)
    names = sorted(p[:-len(".boh")] for p in os.listdir(archive_dir)
                   if p.endswith(".boh"))

    failures = []
    headers = {}
    for name in names:
        with open(os.path.join(archive_dir, name + ".boh"), "rb") as fh:
            buf = fh.read()
        row = {"archive_bytes": len(buf), "archive_sha256": sha256(buf)}
        headers[name] = row

        frozen_path = os.path.join(args.frozen, name + ".boh")
        if os.path.exists(frozen_path):
            with open(frozen_path, "rb") as fh:
                frozen = fh.read()
            row["frozen_header_bytes"] = len(frozen)
            row["begins_with_frozen_header"] = buf[:len(frozen)] == frozen
        else:
            frozen = None
            row["frozen_header_bytes"] = None
            row["begins_with_frozen_header"] = False
        if not row["begins_with_frozen_header"]:
            failures.append("%s: archive does not begin with the frozen header" % name)

        try:
            dec = decode_archive(buf)
        except FormatError as exc:
            row["decode_error"] = str(exc)
            failures.append("%s: decode error: %s" % (name, exc))
            continue

        files = dec.pop("files")
        row["entries"] = dec["entries"]
        row["files"] = dec["file_count"]
        row["tokens"] = dec["tokens"]
        row["escapes"] = dec["escapes"]
        row["header_bytes"] = dec["header_bytes"]
        row["payload_bytes"] = dec["payload_bytes"]
        row["payload_bits_used"] = dec["payload_bits_used"]
        row["padding_bits"] = dec["padding_bits"]
        row["padding_all_zero"] = dec["padding_all_zero"]
        # Informational: FORMAT.md calls magic, entry count, dictionary and
        # code table "the header"; is the frozen file exactly those bytes?
        row["frozen_file_is_exactly_the_header"] = (
            frozen is not None and len(frozen) == dec["header_bytes"])

        row["file_count_equals_manifest"] = len(files) == len(sources)
        equal = 0
        differing = []
        for i in range(min(len(files), len(sources))):
            if files[i] == sources[i]:
                equal += 1
            else:
                differing.append(manifest["files"][i]["path"])
        row["files_equal_to_source"] = equal
        row["files_differing_from_source"] = len(differing)
        if differing:
            row["first_differing_files"] = differing[:10]
        row["all_files_equal"] = (
            row["file_count_equals_manifest"] and not differing)
        if not row["file_count_equals_manifest"]:
            failures.append("%s: archive holds %d files, manifest lists %d"
                            % (name, len(files), len(sources)))
        if differing:
            failures.append("%s: %d decoded files differ from their source"
                            % (name, len(differing)))

    out = {
        "schema": "objective-holdout-v1/independent-decode/1",
        "decoder": "independent_decode.py, written from FORMAT.md alone",
        "set": set_name,
        "set_manifest": args.set_path,
        "set_manifest_sha256": sha256(manifest_bytes),
        "root": args.root,
        "manifest_files": len(sources),
        "source_bytes": sum(len(s) for s in sources),
        "source_files_match_manifest_sha256_and_size": sources_match_manifest,
        "archives": len(names),
        "headers": headers,
    }
    if not sources_match_manifest:
        failures.append("a source file does not match the sha256 or size in the manifest")

    # Compare with the frozen scoring command's own report.
    results_path = os.path.join(args.out, "results-%s.json" % set_name)
    with open(results_path, "rb") as fh:
        results_bytes = fh.read()
    results = json.loads(results_bytes)
    out["compared_with"] = results_path
    out["compared_with_sha256"] = sha256(results_bytes)
    reported = results["headers"]
    out["archives_without_a_results_row"] = sorted(set(names) - set(reported))
    out["results_rows_without_an_archive"] = sorted(set(reported) - set(names))
    frozen_names = sorted(p[:-len(".boh")] for p in os.listdir(args.frozen)
                          if p.endswith(".boh"))
    out["frozen_headers_without_an_archive"] = sorted(set(frozen_names) - set(names))
    for key in ("archives_without_a_results_row",
                "results_rows_without_an_archive",
                "frozen_headers_without_an_archive"):
        if out[key]:
            failures.append("%s: %s" % (key, ", ".join(out[key])))

    for name in names:
        row = headers[name]
        if name not in reported or "decode_error" in row:
            row["ok"] = False
            continue
        rep = reported[name]
        pairs = [
            ("archive_bytes", row["archive_bytes"], rep["bytes"]["complete"],
             "bytes.complete"),
            ("tokens", row["tokens"], rep["bit_parse_tokens"],
             "bit_parse_tokens"),
            ("escapes", row["escapes"], rep["escapes_in_bit_parse"],
             "escapes_in_bit_parse"),
            ("entries", row["entries"], rep["entries"], "entries"),
        ]
        cmp = {}
        for mine, got, want, theirs in pairs:
            cmp[mine] = {"decoded": got, "results_field": theirs,
                         "results_value": want, "equal": got == want}
            if got != want:
                failures.append("%s: %s decoded %r, results %s is %r"
                                % (name, mine, got, theirs, want))
        row["compared_with_results"] = cmp
        row["ok"] = (row["begins_with_frozen_header"] and row["all_files_equal"]
                     and all(c["equal"] for c in cmp.values()))

    out["failures"] = failures
    out["all_ok"] = not failures

    decode_path = os.path.join(args.out, "decode-%s.json" % set_name)
    with open(decode_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=False)
        fh.write("\n")

    for name in names:
        row = headers[name]
        if "decode_error" in row:
            print("%-18s DECODE ERROR: %s" % (name, row["decode_error"]))
            continue
        print("%-18s bytes %7d  entries %5d  files %4d  tokens %7d  escapes %6d  "
              "frozen-prefix %s  files-equal %d/%d  %s"
              % (name, row["archive_bytes"], row["entries"], row["files"],
                 row["tokens"], row["escapes"],
                 "yes" if row["begins_with_frozen_header"] else "NO",
                 row["files_equal_to_source"], len(sources),
                 "ok" if row.get("ok") else "FAIL"))
    print("set %s: %d archives, %s; wrote %s"
          % (set_name, len(names),
             "all checks passed" if not failures else "%d FAILURES" % len(failures),
             decode_path))
    for line in failures:
        print("FAIL " + line)
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
