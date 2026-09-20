"""Pin and adapt the retained native P for aligned training-data observation.

No predictor values or coder operations change. Existing --save-ppmd-probs
selects the observer and additionally writes <path>.tokens: (token, marker)
byte pairs at TransformerByteUpdate. Marker 0=continuation, 1=first model step,
2=piece-ending token not stepped. The companion prior row predicts the NEXT
token; a last-of-piece row cannot be paired across that reset.
"""
from __future__ import annotations

import hashlib
import io
from pathlib import Path, PurePosixPath
import zipfile


PARENT_ZIP_SHA256 = "c44d941f95bd8504d63ed6ea5112af3ce15aeffb6874ebddb66596ce083c3cf6"
SOURCE_PREIMAGES = {
    "src/predictor.h": "46a2118fd2e8b01d60668faae0c0c381845cda44015e10f1ca921b0df8611040",
    "src/predictor.cpp": "719e2a2bfc2a061630e69085737314598f4903bca420f8973242ab480c4949b1",
    "src/runner.cpp": "e8b9bc757902006bf0d2b30e1461276b172c883cece6d3c9eb3df03c804924bf",
}
TRAINED_VOCAB = bytes([232, 22, 4, 0, 255, 255, 255, 3, 1, 252, 15, 249, 254, 255, 255, 7] + [255] * 16)
ARTICLE_SEPARATOR = bytes.fromhex("08 08 25 ac 65 27 05 08 08 08 08 25 ac 68 27")

CHANGES = {
    "src/predictor.h": [
        ('  void Pretrain(int bit);', '  void Pretrain(int bit);\n  void FinishTrainingCapture();'),
        ('  void TransformerByteUpdate();',
         '  void TransformerByteUpdate();\n  FILE* training_tokens_ = nullptr;'),
    ],
    "src/predictor.cpp": [
        ('    ppmd_probs_writer_.reset(new HalfFileWriter(options.save_ppmd_probs));',
         '''    ppmd_probs_writer_.reset(new HalfFileWriter(options.save_ppmd_probs));
    if (options.transformer_weights.empty() || options.ppmd_only || options.load_transformer_probs.size())
      Fail("training capture requires the native transformer and live PPMD");
    const std::string token_path = options.save_ppmd_probs + ".tokens";
    training_tokens_ = std::fopen(token_path.c_str(), "wbx");
    if (!training_tokens_) Fail("cannot create training tokens");'''),
        ('  if (last_of_piece) {\n    // The next token starts a fresh context;',
         '''  if (training_tokens_) {
    const char row[2] = {char(token), char(last_of_piece ? 2 : article_tokens_ == 1 ? 1 : 0)};
    if (std::fwrite(row, 1, sizeof(row), training_tokens_) != sizeof(row))
      Fail("cannot write training tokens");
  }
  if (last_of_piece) {
    // The next token starts a fresh context;'''),
        ('void Predictor::LoadTransformerProbs() {',
         '''void Predictor::FinishTrainingCapture() {
  if (!training_tokens_) return;
  if (std::fclose(training_tokens_)) Fail("cannot close training tokens");
  training_tokens_ = nullptr;
}

void Predictor::LoadTransformerProbs() {'''),
    ],
    "src/runner.cpp": [
        ('  Compress(temp_bytes, &temp_in, &data_out, output_bytes, &p);',
         '  Compress(temp_bytes, &temp_in, &data_out, output_bytes, &p);\n  p.FinishTrainingCapture();'),
        ('  Decompress(*output_bytes, &data_in, &temp_out, &p);',
         '  Decompress(*output_bytes, &data_in, &temp_out, &p);\n  p.FinishTrainingCapture();'),
    ],
}


def source_members(source_zip: Path) -> dict[str, bytes]:
    raw = source_zip.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PARENT_ZIP_SHA256:
        raise ValueError("retained native P ZIP preimage mismatch")
    members = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        for info in archive.infolist():
            path = PurePosixPath(info.filename)
            if path.is_absolute() or ".." in path.parts or info.filename in members:
                raise ValueError("unsafe or duplicate native source member")
            if info.is_dir():
                continue
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("native source member is a symlink")
            members[info.filename] = archive.read(info)
    return members


def adapt(members: dict[str, bytes]):
    """Return new source bytes and per-file preimage/postimage identities."""
    output = dict(members)
    changes = []
    for path, replacements in CHANGES.items():
        before = members[path]
        if hashlib.sha256(before).hexdigest() != SOURCE_PREIMAGES[path]:
            raise ValueError("native source preimage mismatch: " + path)
        text = before.decode()
        for old, new in replacements:
            if text.count(old) != 1:
                raise ValueError(f"ambiguous training-capture anchor: {path}: {old}")
            text = text.replace(old, new)
        output[path] = text.encode()
        changes.append({"path": path, "preimage_sha256": hashlib.sha256(before).hexdigest(),
                        "postimage_sha256": hashlib.sha256(output[path]).hexdigest()})
    return output, changes


def validate_rows(token_rows: bytes, prior_bytes: int, *, expected_tokens: bytes | None = None):
    """Reject shifted populations and malformed reset markers before training."""
    if not token_rows or len(token_rows) % 2:
        raise ValueError("incomplete native token/marker rows")
    tokens, markers = token_rows[::2], token_rows[1::2]
    if len(tokens) * 205 * 2 != prior_bytes:
        raise ValueError("native token/prior population mismatch")
    if expected_tokens is not None and tokens != expected_tokens:
        raise ValueError("captured tokens differ from the actual modeled WRT stream")
    if any(t >= 205 for t in tokens) or any(m > 2 for m in markers):
        raise ValueError("invalid native token or reset marker")
    if markers[0] not in (1, 2):
        raise ValueError("capture does not begin at a native piece boundary")
    for previous, marker in zip(markers, markers[1:]):
        if previous == 2 and marker not in (1, 2):
            raise ValueError("missing native piece start")
        if previous != 2 and marker == 1:
            raise ValueError("unexplained native piece reset")
    return {"rows": len(tokens), "first_steps": markers.count(1),
            "piece_ending_rows": markers.count(2),
            "eligible_next_token_rows": sum(m != 2 for m in markers[:-1])}


def expected_rows(stored: bytes, raw_bytes: int) -> bytes:
    """Independent mapping of the retained single-TEXT preprocessing fixture.

Five-byte stored wrapper and five-byte outer TEXT header precede the actual
modeled WRT stream. This bounded profile must not be applied to full-enwik9
preprocessing or multi-block fixtures by guessing offsets.
"""
    if stored[:10] != b"\x80\0\0\0\0\x07" + raw_bytes.to_bytes(4, "big"):
        raise ValueError("not the declared single-TEXT stored fixture")
    vocabulary = [v for v in range(256) if TRAINED_VOCAB[v // 8] & (1 << (v % 8))]
    mapping = {v: i for i, v in enumerate(vocabulary)}
    if len(vocabulary) != 205:
        raise ValueError("native vocabulary differs")
    try:
        tokens = bytes(mapping[v] for v in stored[10:])
    except KeyError as error:
        raise ValueError("modeled byte outside native vocabulary") from error
    result = bytearray()
    count = 0
    for index, token in enumerate(tokens):
        count += 1
        last = tokens[max(0, index - 14):index + 1] == ARTICLE_SEPARATOR or count == 131072
        result.extend((token, 2 if last else 1 if count == 1 else 0))
        if last:
            count = 0
    return bytes(result)


def training_windows(rows: bytes, anchors: list[int], length: int) -> list[int]:
    """Choose positions from reset geometry alone, before any model fitting."""
    markers = rows[1::2]
    selected = []
    for anchor in anchors:
        for start in range(anchor, len(markers) - length):
            if 2 not in markers[start:start + length] and 1 not in markers[start + 1:start + length + 1]:
                selected.append(start)
                break
        else:
            raise ValueError("no complete training window after frozen anchor")
    return selected
