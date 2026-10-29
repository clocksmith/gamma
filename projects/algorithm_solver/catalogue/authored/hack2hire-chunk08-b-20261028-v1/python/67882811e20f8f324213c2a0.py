"""Hack2Hire 67882811e20f8f324213c2a0 (Substring Wrapper) over an INFERRED spec; qualification unknown."""

def solve(s, elements):
    children = [{}]
    terminal = [False]
    for e in elements:
        node = 0
        for ch in e:
            nxt = children[node].get(ch)
            if nxt is None:
                nxt = len(children)
                children[node][ch] = nxt
                children.append({})
                terminal.append(False)
            node = nxt
        terminal[node] = True
    out = []
    for word in s.split(' '):
        n = len(word)
        piece = word
        for start in range(n):
            node, best, p = 0, 0, start
            while p < n:
                node = children[node].get(word[p])
                if node is None:
                    break
                p += 1
                if terminal[node]:
                    best = p - start
            if best:
                piece = word[:start] + '[' + word[start:start + best] + ']' + word[start + best:]
                break
        out.append(piece)
    return ' '.join(out)


class Solution:
    def wrapSubstrings(self, s, elements):
        return solve(s, elements)
