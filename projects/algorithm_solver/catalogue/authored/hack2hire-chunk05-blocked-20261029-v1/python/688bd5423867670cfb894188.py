"""Hack2Hire 688bd5423867670cfb894188 (Detect Abusive Words) over an INFERRED spec; qualification unknown."""


def solve(words, substitutions, comment):
    children = [{}]
    ends = [False]
    for word in words:
        node = 0
        for ch in word:
            nxt = children[node].get(ch)
            if nxt is None:
                nxt = len(children)
                children[node][ch] = nxt
                children.append({})
                ends.append(False)
            node = nxt
        ends[node] = True
    letters = {}
    for symbol, letter in substitutions:
        options = letters.setdefault(symbol, [])
        if letter not in options:
            options.append(letter)
    found = []
    for index, token in enumerate(comment.split(' ')):
        # trie nodes have one parent each, so distinct steps never reach the same node twice
        current = [0]
        for ch in token:
            options = (ch,) if 'a' <= ch <= 'z' else letters.get(ch, ())
            following = []
            for node in current:
                edges = children[node]
                for letter in options:
                    nxt = edges.get(letter)
                    if nxt is not None:
                        following.append(nxt)
            current = following
            if not current:
                break
        if any(ends[node] for node in current):
            found.append(index)
    return found


class Solution:
    def detectAbusiveWords(self, words, substitutions, comment):
        return solve(words, substitutions, comment)
