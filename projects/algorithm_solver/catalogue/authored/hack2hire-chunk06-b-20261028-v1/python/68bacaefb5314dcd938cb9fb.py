"""Hack2Hire 68bacaefb5314dcd938cb9fb (Highlight Phrases in Review) over an INFERRED spec; qualification unknown."""

ALNUM = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')


def solve(review, mapping):
    trie, category = [{}], [None]
    for phrase, cat in mapping:
        node = 0
        for ch in phrase.lower():
            nxt = trie[node].get(ch)
            if nxt is None:
                nxt = len(trie)
                trie[node][ch] = nxt
                trie.append({})
                category.append(None)
            node = nxt
        if category[node] is None:
            category[node] = cat
    low, n = review.lower(), len(review)
    out, i = [], 0
    while i < n:
        if review[i] in ALNUM and (i == 0 or review[i - 1] not in ALNUM):
            node, j, best, best_cat = 0, i, -1, None
            while j < n:
                node = trie[node].get(low[j])
                if node is None:
                    break
                j += 1
                if category[node] is not None and (j == n or review[j] not in ALNUM):
                    best, best_cat = j, category[node]
            if best >= 0:
                out.append('[' + best_cat + ']{' + review[i:best] + '}')
                i = best
                continue
        out.append(review[i])
        i += 1
    return ''.join(out)


class Solution:
    def highlightReview(self, review, mapping):
        return solve(review, mapping)
