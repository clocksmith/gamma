"""xml_parser — Phase 1: extract XML framing fields, leave <text> intact.

Per the build order:
  Phase 1 extracts <id>, <title>, <timestamp>, <username>, <ip>,
  <comment>. The entire <text xml:space="preserve">...</text> block is
  left untouched in the scaffold and will be addressed in Phase 5.

Each field VALUE is replaced in the scaffold with a 4-byte sentinel
unique to that channel. Sentinels are 4-byte sequences MUST NOT appear
anywhere in the input — if they do, the encoder must abort typed mode
and fall back to literal storage.

Output:
  scaffold: bytes (input with field values replaced by sentinels)
  channels: dict[name -> list[bytes]] (captured values in document order)
"""

from __future__ import annotations

import re

# Sentinels: 4-byte sequences. Bytes 0x00 and 0xFE are essentially absent
# from well-formed enwik9 (which is UTF-8 ASCII). The trailing byte
# distinguishes the channel.
SENT = {
    "title":     b"\x00\x00\xFE\xF1",
    "id":        b"\x00\x00\xFE\xF2",
    "timestamp": b"\x00\x00\xFE\xF4",
    "username":  b"\x00\x00\xFE\xF5",
    "ip":        b"\x00\x00\xFE\xF6",
    "comment":   b"\x00\x00\xFE\xF8",
}

CHANNEL_NAMES = list(SENT.keys())

# Patterns. <comment> may contain HTML entities and even nested-looking
# constructs, so it gets DOTALL and non-greedy. Other fields are
# constrained to non-tag content between their tags.
_RE_COMMENT   = re.compile(rb"(<comment>)(.*?)(</comment>)", re.DOTALL)
_RE_TITLE     = re.compile(rb"(<title>)([^<]*)(</title>)")
_RE_TIMESTAMP = re.compile(rb"(<timestamp>)([^<]*)(</timestamp>)")
_RE_USERNAME  = re.compile(rb"(<username>)([^<]*)(</username>)")
_RE_IP        = re.compile(rb"(<ip>)([^<]*)(</ip>)")
_RE_ID        = re.compile(rb"(<id>)([^<]*)(</id>)")

# Order: <comment> first because it can be multi-line. <id> last because
# its pattern is the most permissive and can collide with already-extracted
# constructs if applied earlier.
_FIELD_REGEX = [
    ("comment", _RE_COMMENT),
    ("title", _RE_TITLE),
    ("timestamp", _RE_TIMESTAMP),
    ("username", _RE_USERNAME),
    ("ip", _RE_IP),
    ("id", _RE_ID),
]


def has_sentinel_collision(data: bytes) -> bool:
    return any(s in data for s in SENT.values())


def extract_xml_channels(
    data: bytes,
) -> tuple[bytes, dict[str, list[bytes]]]:
    """Return (scaffold, channels). channels has every name with a list
    (possibly empty)."""
    if has_sentinel_collision(data):
        raise ValueError("sentinel collision in input; cannot use typed mode")
    scaffold = data
    channels: dict[str, list[bytes]] = {n: [] for n in CHANNEL_NAMES}
    for name, regex in _FIELD_REGEX:
        captured: list[bytes] = []
        sent = SENT[name]

        def repl(m: re.Match, _captured=captured, _sent=sent) -> bytes:
            _captured.append(m.group(2))
            return m.group(1) + _sent + m.group(3)

        scaffold = regex.sub(repl, scaffold)
        channels[name] = captured
    return scaffold, channels


def reconstruct(
    scaffold: bytes, channels: dict[str, list[bytes]]
) -> bytes:
    """Inverse of extract_xml_channels. Walks the scaffold and replaces
    each sentinel with the next value from the named channel."""
    iters = {name: iter(channels[name]) for name in CHANNEL_NAMES}
    out = bytearray()
    pos = 0
    n = len(scaffold)
    while pos < n:
        match_name = None
        if pos + 4 <= n:
            window = scaffold[pos : pos + 4]
            for name, sent in SENT.items():
                if window == sent:
                    match_name = name
                    break
        if match_name is None:
            out.append(scaffold[pos])
            pos += 1
        else:
            try:
                value = next(iters[match_name])
            except StopIteration:
                raise ValueError(
                    f"channel underflow: {match_name} at scaffold pos {pos}"
                )
            out.extend(value)
            pos += 4
    for name, it in iters.items():
        try:
            next(it)
            raise ValueError(f"channel overflow: {name} has unconsumed values")
        except StopIteration:
            pass
    return bytes(out)
