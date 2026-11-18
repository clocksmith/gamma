"""Post-hoc audit: which token does v4's discoverSupportAnchors pick on each v4 confirmation specialty?

No model is run and nothing is scored. Usage:
  python -B anchor_audit.py ../query_swiglu_fastweight_v4 QWEN_TOKENIZER_JSON GEMMA_TOKENIZER_JSON
"""
import sys, collections
from tokenizers import Tokenizer
sys.path.insert(0, sys.argv[1])
import tasks_v4

def discover(ids, nl):
    lines, start = [], 0
    for i, t in enumerate(ids):
        if t == nl:
            if i - start >= 6: lines.append((start, i))
            start = i + 1
    pos_by_tok = collections.OrderedDict()
    for li, (s, e) in enumerate(lines):
        last = collections.OrderedDict()
        for p in range(max(s + 3, e - 8), e):
            if p <= e - 2:
                last[ids[p]] = p
        for tok, p in last.items():
            pos_by_tok.setdefault(tok, []).append((li, p, s, e))
    best, best_count, best_span = -1, 0, float('inf')
    for tok, arr in pos_by_tok.items():
        if len(arr) < 4: continue
        if len({tuple(ids[p + 1:e]) for _, p, _, e in arr}) < 2: continue
        mean = sum(e - p for _, p, _, e in arr) / len(arr)
        if len(arr) > best_count or (len(arr) == best_count and mean < best_span):
            best, best_count, best_span = tok, len(arr), mean
    return best, pos_by_tok.get(best, [])

for name, path in (('qwen', sys.argv[2]), ('gemma', sys.argv[3])):
    tok = Tokenizer.from_file(path)
    enc = lambda s: tok.encode(s, add_special_tokens=False).ids
    nl = enc('\n')[-1]
    seen = {}
    for t in tasks_v4.build_v4_unseen_tasks(1040001, 8):
        if t['specialty_id'] in seen: continue
        ids = enc(t['support_text'])
        a, arr = discover(ids, nl)
        lens = sorted({e - p - 1 for _, p, _, e in arr})
        q_last = enc(t['query_line'])[-1]
        true_len = len(enc(' ' + t['expected']))
        seen[t['specialty_id']] = 1
        print(f"{name:6s}{t['specialty_id'][:44]:46s} anchor={tok.decode([a])!r:7s} lines={len(arr):2d} answerLen={lens} query_ends_with={tok.decode([q_last])!r:6s} same={a == q_last} expected_tokens={true_len}")
