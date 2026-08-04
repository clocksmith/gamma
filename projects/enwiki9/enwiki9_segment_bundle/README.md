# enwiki9 five-segment proof-carrying bundle

This is a working **outer compressor, decompressor, scorer, and certificate generator** for the five independent 200 MB segment construction discussed in the session.

It does **not** invent the five winning segment codecs. Each accepted segment solution must be supplied as an exact ZIP package whose payload plus package is at most `20,190,000` bytes. The outer program verifies and composes those packages.

## Segment package ABI

Each segment package is a ZIP file containing a root-level `codec.json`:

```json
{
  "schema": "enwiki9_segment_codec/v1",
  "codec_id": "segment-0-solution-v1",
  "segment_index": 0,
  "prepare": [],
  "compress": ["python3", "codec.py", "compress", "{input}", "{output}"],
  "decompress": ["python3", "codec.py", "decompress", "{input}", "{output}"],
  "environment": {}
}
```

The package can contain Python, C++, binaries, source, tables, dictionaries, or models. Every byte in the ZIP is counted. `prepare` is optional and runs in a fresh extraction before the codec command. Commands are argument arrays, never shell strings.

The wrapper safely extracts ZIP files, forbids path traversal and symlinks, verifies package hashes, and runs each codec in a fresh directory. A fixed external VM or OS sandbox is still required to enforce no-network and exact resource limits.

## Commands

Create a deterministic stored ZIP from a codec directory:

```bash
python3 enwiki9_bundle.py pack-directory \
  --source segment-0-source \
  --output segment-0.zip
```

Create an archive:

```bash
python3 enwiki9_bundle.py compress \
  --manifest manifest.json \
  --competition-profile \
  --input enwik9 \
  --archive enwiki9.bundle
```

Create the strongest local certificate. This independently compresses each segment twice, checks deterministic payload identity, roundtrips each segment, builds the full archive, decodes it, checks the complete one-billion-byte output, and calculates the exact score:

```bash
python3 enwiki9_bundle.py certify \
  --manifest manifest.json \
  --competition-profile \
  --input enwik9 \
  --archive enwiki9.bundle \
  --certificate certificate.json
```

Decode:

```bash
python3 enwiki9_bundle.py decompress \
  --manifest manifest.json \
  --competition-profile \
  --archive enwiki9.bundle \
  --output enwik9.restored
```

Inspect or score:

```bash
python3 enwiki9_bundle.py inspect --archive enwiki9.bundle
python3 enwiki9_bundle.py score \
  --manifest manifest.json \
  --competition-profile \
  --archive enwiki9.bundle
```

## Exact accounting

For each segment:

```text
segment score = segment payload bytes + segment package ZIP bytes
```

The wrapper requires every segment score to be at most `20,190,000` bytes.

The common overhead is:

```text
outer package bytes + manifest bytes + archive header/footer bytes
```

It must be at most `100,000` bytes.

The final score is:

```text
archive bytes
+ outer package bytes
+ manifest bytes
+ all five segment package bytes
```

If all frozen budgets pass, the score is below `101,101,101` and therefore also below `107,000,000`.

## Important boundary

The included LZMA codec is only a functional example. It is not expected to satisfy the segment budgets. The missing scientific work is still the construction of five independent codecs whose exact package-plus-payload sizes meet the required limits.
