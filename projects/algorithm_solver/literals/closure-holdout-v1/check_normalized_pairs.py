#!/usr/bin/env python3
"""Checks for the proposition in NORMALIZED-PAIRS.md, by exact shortest-path parsing on small corpora.

    python3 -I check_normalized_pairs.py [TRIALS] [SEED]

1. The six-document counterexample: a fragment that needs three tokens beats every two-token candidate on normalized
   gain, because its premise fails (the expanded parse is not optimal under the old vocabulary).
2. Randomized check of the proposition: on random small corpora and vocabularies, for every candidate w with
   s_V(w) >= 3 whose expanded parse is optimal under V (alignment penalty 0), some adjacent pair of a minimum
   V-spelling of w has gain at least Delta(w) / (s_V(w) - 1). Also counts candidates whose penalty is positive and
   how often one of them beats every pair (the premise matters).
Exits non-zero if the proposition fails on any instance.
"""
import random
import sys
from fractions import Fraction


def best_parse(text, vocab):
    """Minimum token count and one minimum parse (list of pieces)."""
    n = len(text)
    best = [0] + [10**9] * n
    back = [None] * (n + 1)
    for i in range(n):
        if best[i] >= 10**9:
            continue
        for j in range(i + 1, n + 1):
            if text[i:j] in vocab and best[i] + 1 < best[j]:
                best[j] = best[i] + 1
                back[j] = i
    pieces, j = [], n
    while j > 0:
        i = back[j]
        pieces.append(text[i:j])
        j = i
    return best[n], pieces[::-1]


def total(docs, vocab):
    return sum(best_parse(d, vocab)[0] for d in docs)


def uses_after(docs, vocab, w):
    """Uses of w in one optimal parse of every document under vocab + {w}."""
    v = vocab | {w}
    return sum(sum(1 for p in best_parse(d, v)[1] if p == w) for d in docs)


def counterexample():
    docs = ['Xabcd', 'Wabcd', 'abcdY', 'abcdZ', 'Uabcd', 'Vabcd']
    vocab = set(''.join(docs)) | {'bc', 'Xab', 'Wab', 'cdY', 'cdZ', 'Ua', 'Va'}
    base = total(docs, vocab)
    rows = []
    for w in {d[i:j] for d in docs for i in range(len(d)) for j in range(i + 2, len(d) + 1)} - vocab:
        s = best_parse(w, vocab)[0]
        g = base - total(docs, vocab | {w})
        if g > 0:
            rows.append((Fraction(g, s - 1), g, s, w))
    rows.sort(reverse=True)
    top = rows[0]
    best_pair = max((r for r in rows if r[2] == 2), default=None)
    m = uses_after(docs, vocab, top[3])
    penalty = base - (total(docs, vocab | {top[3]}) + m * (top[2] - 1))
    print(f'counterexample: {top[3]!r} needs {top[2]} tokens, gains {top[1]}, scores {top[0]}; best two-token candidate '
          f'{best_pair[3]!r} scores {best_pair[0]}; alignment penalty of the winner: {-penalty}')
    return top[2] >= 3 and best_pair is not None and top[0] > best_pair[0] and penalty != 0


def randomized(trials, seed):
    rng = random.Random(seed)
    checked = premise_true = premise_false = false_wins = 0
    for _ in range(trials):
        k = rng.choice([2, 3, 3, 4])
        letters = 'abcd'[:k]
        docs = [''.join(rng.choice(letters) for _ in range(rng.randint(4, 11))) for _ in range(rng.randint(1, 5))]
        vocab = set(''.join(docs))
        frags = sorted({d[i:j] for d in docs for i in range(len(d)) for j in range(i + 2, min(len(d), i + 6) + 1)})
        for f in rng.sample(frags, min(len(frags), rng.randint(0, 5))):
            vocab.add(f)
        base = total(docs, vocab)
        pair_scores = []
        cands = sorted({d[i:j] for d in docs for i in range(len(d)) for j in range(i + 2, min(len(d), i + 8) + 1)} - vocab)
        gains = {}
        for w in cands:
            gains[w] = base - total(docs, vocab | {w})
        for w in cands:
            s, spelling = best_parse(w, vocab)
            if s == 2 and gains[w] > 0:
                pair_scores.append(gains[w])
        best_pair = max(pair_scores, default=0)
        for w in cands:
            s, spelling = best_parse(w, vocab)
            if s < 3 or gains[w] <= 0:
                continue
            checked += 1
            m = uses_after(docs, vocab, w)
            expanded = total(docs, vocab | {w}) + m * (s - 1)
            if expanded == base:  # premise: the expansion is optimal under the old vocabulary
                premise_true += 1
                pairs = [spelling[i] + spelling[i + 1] for i in range(len(spelling) - 1)]
                best_adjacent = max(gains.get(p, base - total(docs, vocab | {p})) for p in pairs)
                if Fraction(best_adjacent) < Fraction(gains[w], s - 1):
                    print('PROPOSITION FAILS:', {'docs': docs, 'vocab': sorted(vocab), 'w': w, 'spelling': spelling,
                                                 'gain': gains[w], 'uses': m, 'best_adjacent_pair_gain': best_adjacent})
                    return False, (checked, premise_true, premise_false, false_wins)
            else:
                premise_false += 1
                if Fraction(gains[w], s - 1) > best_pair:
                    false_wins += 1
    return True, (checked, premise_true, premise_false, false_wins)


def main():
    trials = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    ok_ce = counterexample()
    ok, (checked, t, f, wins) = randomized(trials, seed)
    print(f'randomized: {trials} corpora, {checked} candidates needing >= 3 tokens; premise holds for {t}, '
          f'proposition held on all of them: {ok}; premise fails for {f}, and {wins} of those beat every two-token candidate')
    sys.exit(0 if ok and ok_ce else 1)


if __name__ == '__main__':
    main()
