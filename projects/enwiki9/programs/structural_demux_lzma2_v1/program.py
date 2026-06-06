from __future__ import annotations

import lzma

MAGIC = b"SDM1"
MODE_RAW = 0
MODE_DEMUX = 1
MODE_BLOCKS = 2
ESC = 1
ESC_LIT = 0
ESC_WORD = 1
ESC_NUM = 2
ESC_PROSE_BLOCK = 3
ESC_NUM_BLOCK = 4
PRESET = 9 | lzma.PRESET_EXTREME
FILTERS = [{"id": lzma.FILTER_LZMA2, "preset": PRESET, "dict_size": 1 << 30}]
THRESHOLDS = ()
PROSE_FIELDS = (
    (b'<text xml:space="preserve">', b"</text>"),
    (b"<title>", b"</title>"),
    (b"<comment>", b"</comment>"),
    (b"<username>", b"</username>"),
    (b"<sitename>", b"</sitename>"),
    (b"<base>", b"</base>"),
)
VALUE_FIELDS = (
    (b"<timestamp>", b"</timestamp>"),
    (b"<id>", b"</id>"),
    (b"<ip>", b"</ip>"),
)
FIELDS = tuple((a, b, ESC_PROSE_BLOCK) for a, b in PROSE_FIELDS) + tuple(
    (a, b, ESC_NUM_BLOCK) for a, b in VALUE_FIELDS
)
FIELDS = tuple(sorted(FIELDS, key=lambda item: len(item[0]), reverse=True))
_S: dict = {}


def _uvar(n: int) -> bytes:
    out = bytearray()
    while n >= 128:
        out.append((n & 127) | 128)
        n >>= 7
    out.append(n)
    return bytes(out)


def _ruvar(buf: bytes, pos: int) -> tuple[int, int]:
    n = 0
    shift = 0
    while True:
        if pos >= len(buf):
            raise ValueError("truncated varint")
        b = buf[pos]
        pos += 1
        n |= (b & 127) << shift
        if b < 128:
            return n, pos
        shift += 7


def _lz(data: bytes) -> bytes:
    return lzma.compress(data, format=lzma.FORMAT_XZ, filters=FILTERS)


def _unlz(data: bytes) -> bytes:
    return lzma.decompress(data)


def _is_alpha(b: int) -> bool:
    return (65 <= b <= 90) or (97 <= b <= 122) or b == 95 or b >= 128


def _put_skel(out: bytearray, b: int) -> None:
    if b == ESC:
        out.extend((ESC, ESC_LIT))
    else:
        out.append(b)


def _split(data: bytes, min_word: int) -> tuple[bytes, bytes, bytes]:
    skel = bytearray()
    words = bytearray()
    nums = bytearray()
    i = 0
    n = len(data)
    in_tag = False
    while i < n:
        b = data[i]
        if b == 60:
            in_tag = True
            _put_skel(skel, b)
            i += 1
            continue
        if in_tag:
            _put_skel(skel, b)
            if b == 62:
                in_tag = False
            i += 1
            continue
        if 48 <= b <= 57:
            j = i + 1
            while j < n and 48 <= data[j] <= 57:
                j += 1
            chunk = data[i:j]
            nums.extend(chunk)
            skel.extend((ESC, ESC_NUM))
            skel.extend(_uvar(len(chunk)))
            i = j
            continue
        if _is_alpha(b):
            j = i + 1
            while j < n and _is_alpha(data[j]):
                j += 1
            chunk = data[i:j]
            if len(chunk) >= min_word:
                words.extend(chunk)
                skel.extend((ESC, ESC_WORD))
                skel.extend(_uvar(len(chunk)))
            else:
                for c in chunk:
                    _put_skel(skel, c)
            i = j
            continue
        _put_skel(skel, b)
        i += 1
    return bytes(skel), bytes(words), bytes(nums)


def _split_blocks(data: bytes) -> tuple[bytes, bytes, bytes]:
    skel = bytearray()
    prose = bytearray()
    nums = bytearray()
    i = 0
    n = len(data)
    while i < n:
        matched = False
        for open_tag, close_tag, tag in FIELDS:
            if not data.startswith(open_tag, i):
                continue
            start = i + len(open_tag)
            end = data.find(close_tag, start)
            if end < 0:
                break
            for c in open_tag:
                _put_skel(skel, c)
            body = data[start:end]
            if tag == ESC_PROSE_BLOCK:
                prose.extend(body)
            else:
                nums.extend(body)
            skel.extend((ESC, tag))
            skel.extend(_uvar(len(body)))
            for c in close_tag:
                _put_skel(skel, c)
            i = end + len(close_tag)
            matched = True
            break
        if matched:
            continue
        _put_skel(skel, data[i])
        i += 1
    return bytes(skel), bytes(prose), bytes(nums)


def _join(skel: bytes, words: bytes, nums: bytes) -> bytes:
    out = bytearray()
    wp = 0
    np = 0
    i = 0
    n = len(skel)
    while i < n:
        b = skel[i]
        i += 1
        if b != ESC:
            out.append(b)
            continue
        if i >= n:
            raise ValueError("trailing escape")
        tag = skel[i]
        i += 1
        if tag == ESC_LIT:
            out.append(ESC)
        elif tag == ESC_WORD:
            size, i = _ruvar(skel, i)
            out.extend(words[wp:wp + size])
            wp += size
        elif tag == ESC_NUM:
            size, i = _ruvar(skel, i)
            out.extend(nums[np:np + size])
            np += size
        else:
            raise ValueError("bad escape tag")
    if wp != len(words) or np != len(nums):
        raise ValueError("unused demux bytes")
    return bytes(out)


def _join_blocks(skel: bytes, prose: bytes, nums: bytes) -> bytes:
    out = bytearray()
    pp = 0
    np = 0
    i = 0
    n = len(skel)
    while i < n:
        b = skel[i]
        i += 1
        if b != ESC:
            out.append(b)
            continue
        if i >= n:
            raise ValueError("trailing escape")
        tag = skel[i]
        i += 1
        if tag == ESC_LIT:
            out.append(ESC)
        elif tag == ESC_PROSE_BLOCK:
            size, i = _ruvar(skel, i)
            out.extend(prose[pp:pp + size])
            pp += size
        elif tag == ESC_NUM_BLOCK:
            size, i = _ruvar(skel, i)
            out.extend(nums[np:np + size])
            np += size
        else:
            raise ValueError("bad block escape tag")
    if pp != len(prose) or np != len(nums):
        raise ValueError("unused block bytes")
    return bytes(out)


def _pack_demux(data: bytes, min_word: int) -> tuple[bytes, dict]:
    skel, words, nums = _split(data, min_word)
    cskel = _lz(skel)
    cwords = _lz(words)
    cnums = _lz(nums)
    body = bytearray(MAGIC)
    body.extend((MODE_DEMUX, min_word))
    for part in (cskel, cwords, cnums):
        body.extend(_uvar(len(part)))
    body.extend(cskel)
    body.extend(cwords)
    body.extend(cnums)
    info = {
        "mode": "demux",
        "min_word": min_word,
        "raw_streams": {
            "syntax_skeleton": len(skel),
            "prose_words": len(words),
            "numeric_values": len(nums),
        },
        "compressed_streams": {
            "syntax_skeleton": len(cskel),
            "prose_words": len(cwords),
            "numeric_values": len(cnums),
        },
    }
    return bytes(body), info


def _pack_blocks(data: bytes) -> tuple[bytes, dict]:
    skel, prose, nums = _split_blocks(data)
    cskel = _lz(skel)
    cprose = _lz(prose)
    cnums = _lz(nums)
    body = bytearray(MAGIC)
    body.append(MODE_BLOCKS)
    for part in (cskel, cprose, cnums):
        body.extend(_uvar(len(part)))
    body.extend(cskel)
    body.extend(cprose)
    body.extend(cnums)
    info = {
        "mode": "block_demux",
        "raw_streams": {
            "syntax_skeleton": len(skel),
            "prose_blocks": len(prose),
            "numeric_values": len(nums),
        },
        "compressed_streams": {
            "syntax_skeleton": len(cskel),
            "prose_blocks": len(cprose),
            "numeric_values": len(cnums),
        },
    }
    return bytes(body), info


def compress(data: bytes) -> bytes:
    raw = MAGIC + bytes([MODE_RAW]) + _lz(data)
    best = raw
    best_info = {"mode": "raw_lzma2", "archive": len(raw)}
    candidates = {"raw_lzma2": len(raw)}
    details = {}
    cand, info = _pack_blocks(data)
    candidates["block_demux"] = len(cand)
    details["block_demux"] = dict(info)
    if len(cand) < len(best):
        best = cand
        best_info = dict(info)
        best_info["archive"] = len(cand)
    for min_word in THRESHOLDS:
        cand, info = _pack_demux(data, min_word)
        key = "word_demux_" + str(min_word)
        candidates[key] = len(cand)
        details[key] = dict(info)
        if len(cand) < len(best):
            best = cand
            best_info = dict(info)
            best_info["archive"] = len(cand)
    best_info["candidate_archives"] = candidates
    best_info["candidate_details"] = details
    _S.clear()
    _S.update(best_info)
    return best


def decompress(data: bytes) -> bytes:
    if not data.startswith(MAGIC):
        raise ValueError("bad magic")
    pos = len(MAGIC)
    mode = data[pos]
    pos += 1
    if mode == MODE_RAW:
        return _unlz(data[pos:])
    if mode == MODE_BLOCKS:
        sizes = []
        for _ in range(3):
            size, pos = _ruvar(data, pos)
            sizes.append(size)
        cskel = data[pos:pos + sizes[0]]
        pos += sizes[0]
        cprose = data[pos:pos + sizes[1]]
        pos += sizes[1]
        cnums = data[pos:pos + sizes[2]]
        skel = _unlz(cskel)
        prose = _unlz(cprose)
        nums = _unlz(cnums)
        _S.clear()
        _S.update({"mode": "block_demux"})
        return _join_blocks(skel, prose, nums)
    if mode != MODE_DEMUX:
        raise ValueError("bad mode")
    min_word = data[pos]
    pos += 1
    sizes = []
    for _ in range(3):
        size, pos = _ruvar(data, pos)
        sizes.append(size)
    cskel = data[pos:pos + sizes[0]]
    pos += sizes[0]
    cwords = data[pos:pos + sizes[1]]
    pos += sizes[1]
    cnums = data[pos:pos + sizes[2]]
    skel = _unlz(cskel)
    words = _unlz(cwords)
    nums = _unlz(cnums)
    _S.clear()
    _S.update({"mode": "demux", "min_word": min_word})
    return _join(skel, words, nums)


def stats() -> dict:
    return dict(_S)
