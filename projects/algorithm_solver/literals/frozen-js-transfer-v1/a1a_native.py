"""Full-file native token-stream and full-table byte-rank checks for A1a."""

import heapq
from importlib.metadata import version
import json

from a1a_fit import E, H
import validate_encoders as V
from tokenizers import Tokenizer
import sentencepiece
import tiktoken


def replay(raw, rank):
    """Independent leftmost, lowest-rank merge, retaining original byte offsets."""
    tokens = [bytes([b]) for b in raw]
    n = len(tokens)
    after = list(range(1, n + 1))
    before = list(range(-1, n - 1))
    queue = []

    def offer(i):
        if i >= 0 and after[i] < n:
            j = after[i]
            score = rank(tokens[i], tokens[j])
            if score is not None:
                heapq.heappush(queue, (score, i, j))

    for i in range(n):
        offer(i)
    while queue:
        score, i, j = heapq.heappop(queue)
        if not tokens[i] or after[i] != j or rank(tokens[i], tokens[j]) != score:
            continue
        tokens[i] += tokens[j]
        tokens[j] = b""
        after[i] = after[j]
        if after[i] < n:
            before[after[i]] = i
        offer(before[i])
        offer(i)
    return [t for t in tokens if t]


def validate_reference():
    if tiktoken.__version__ != "0.14.0":
        raise ValueError("tiktoken must match preregistered 0.14.0")
    pairs = [(b"a", b"a"), (b"a", b"b"), (b"aa", b"a"), (b"ab", b"a"), (b"aa", b"b")]
    order = dict(zip(pairs, range(len(pairs))))
    ranks = V.entries_to_tiktoken_ranks([a + b for a, b in pairs])
    import itertools

    for n in range(8):
        for letters in itertools.product(b"ab", repeat=n):
            raw = bytes(letters)
            if replay(raw, lambda a, b: order.get((a, b))) != V.ref_bpe_merge_replay(
                raw, pairs
            ):
                raise ValueError("ordered-pair reference failure")
            if replay(
                raw, lambda a, b: ranks.get(a + b)
            ) != V.tiktoken_byte_rank_encode(raw, ranks):
                raise ValueError("byte-rank reference failure")
    return {p: version(p) for p in ("tiktoken", "tokenizers", "sentencepiece")}


def native_chain(arm, chain, entries, docs):
    ranks = V.entries_to_tiktoken_ranks(entries)
    enc = tiktoken.Encoding(
        name="bits-a1a", pat_str=r"(?s).+", mergeable_ranks=ranks, special_tokens={}
    )
    expected = V.validate_tiktoken_byte_ranks(ranks)
    if any(b"\0" in w for w in ranks if len(w) > 1):
        raise ValueError("NUL reachability delimiter is present in a learned fragment")
    unreachable = [
        w
        for w, rank in ranks.items()
        if len(w) > 1 and enc._encode_bytes(b"\0" + w + b"\0") != [0, rank, 0]
    ]
    set_unreachable = set(unreachable)
    reachability = {
        "reference": expected,
        "native_unreachable": len(unreachable),
        "mismatch_count": sum(
            (w in set_unreachable) != (V.tiktoken_byte_rank_encode(w, ranks) != [w])
            for w in ranks
            if len(w) > 1
        ),
    }
    merges = None
    if arm == "bpe":
        seen = {w for w in entries if len(w) == 1}
        merges = []
        for a, b in chain["m_lines"]:
            merges.append((a, b))
            seen.add(a + b)
            if len(seen) == len(entries):
                break
        if seen != set(entries):
            raise ValueError("frozen BPE merge prefix disagrees with entries")
    elif arm in ("exact-closed", "pair-byte"):
        merges, unclosed = V.extract_closed_merges(entries)
        if unclosed:
            raise ValueError("unclosed ordered-pair table")
    if merges is not None:
        tok = V.build_hf_byte_bpe_tokenizer(merges)[0]
        rank_pairs = {}
        for i, pair in enumerate(merges):
            rank_pairs.setdefault(pair, i)
    rows = []
    for raw in docs:
        try:
            txt = raw.decode()
        except UnicodeDecodeError:
            txt = None
        ids = enc.encode_ordinary(txt) if txt is not None else enc._encode_bytes(raw)
        pieces = [enc.decode_single_token_bytes(i) for i in ids]
        row = {
            "valid_utf8": txt is not None,
            "tiktoken_tokens": len(ids),
            "tiktoken_roundtrip": b"".join(pieces) == raw,
            "tiktoken_parity": pieces == replay(raw, lambda a, b: ranks.get(a + b)),
        }
        if merges is not None:
            actual = list(
                map(
                    V.decode_bpe_str_to_bytes,
                    tok.encode(V.encode_bytes_to_bpe_str(raw)).tokens,
                )
            )
            row.update(
                hf_tokens=len(actual),
                hf_roundtrip=b"".join(actual) == raw,
                hf_parity=actual == replay(raw, lambda a, b: rank_pairs.get((a, b))),
            )
        rows.append(row)
    return {"reachability": reachability, "files": rows}


def pretrained_controls(docs, singles):
    output = {}
    for path in sorted((E.CHAINS_DIR / "hf_bpe").glob("*.json")):
        model = json.loads(path.read_text())["model"]
        tok = Tokenizer.from_file(str(path))
        merges = [
            pair.split(" ") if isinstance(pair, str) else pair
            for pair in model["merges"]
        ]
        pair_rank = {
            (V.decode_bpe_str_to_bytes(a), V.decode_bpe_str_to_bytes(b)): i
            for i, (a, b) in enumerate(merges)
        }
        entries = list(
            dict.fromkeys(
                [*singles, *(a + b for a, b in pair_rank if 2 <= len(a + b) <= 16)]
            )
        )
        dictionary = H.Dictionary(entries)
        rows = []
        for raw in docs:
            dp = len(H.parse_tokens(dictionary.edges(raw)))
            try:
                txt = raw.decode()
            except UnicodeDecodeError:
                rows.append({"valid_utf8": False, "dp": dp})
                continue
            encoded = tok.encode(txt)
            segments = [
                V.decode_bpe_str_to_bytes(s)
                for s, _ in tok.pre_tokenizer.pre_tokenize_str(txt)
            ]
            pieces = [
                p
                for segment in segments
                for p in replay(segment, lambda a, b: pair_rank.get((a, b)))
            ]
            rows.append(
                {
                    "valid_utf8": True,
                    "dp": dp,
                    "native": len(encoded.ids),
                    "roundtrip": tok.decode(encoded.ids).encode() == raw,
                    "parity": pieces
                    == list(map(V.decode_bpe_str_to_bytes, encoded.tokens)),
                }
            )
        output[path.stem] = rows
    for path in sorted((E.CHAINS_DIR / "sentencepiece").glob("*.model")):
        sp = sentencepiece.SentencePieceProcessor(model_file=str(path))
        pieces = [
            sp.id_to_piece(i).replace("▁", " ").encode()
            for i in range(sp.get_piece_size())
            if not (sp.is_unknown(i) or sp.is_control(i) or sp.is_byte(i))
        ]
        dictionary = H.Dictionary(
            list(dict.fromkeys([*singles, *(p for p in pieces if 1 <= len(p) <= 16)]))
        )
        rows = []
        for raw in docs:
            dp = len(H.parse_tokens(dictionary.edges(raw)))
            try:
                txt = raw.decode()
            except UnicodeDecodeError:
                rows.append({"valid_utf8": False, "dp": dp})
                continue
            ids = sp.encode(txt, out_type=int)
            rows.append(
                {
                    "valid_utf8": True,
                    "dp": dp,
                    "native": len(ids),
                    "roundtrip": sp.decode(ids).encode() == raw,
                }
            )
        output[path.stem] = rows
    return output
