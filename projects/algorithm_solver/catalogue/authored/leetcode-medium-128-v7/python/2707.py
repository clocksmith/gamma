"""2707. Extra Characters in a String: combine suffix dynamic programming with trie walks for dictionary matches."""


def solve(s: str, dictionary: list[str]) -> int:
    """O(W + n * L) expected time and O(W + n) auxiliary space, where W is dictionary size in characters and L is maximum word length; inputs are read-only."""
    children = [{}]
    terminal = [False]
    for word in dictionary:
        node = 0
        for character in word:
            if character not in children[node]:
                children[node][character] = len(children)
                children.append({})
                terminal.append(False)
            node = children[node][character]
        terminal[node] = True
    best = [0] * (len(s) + 1)
    for start in range(len(s) - 1, -1, -1):
        best[start] = best[start + 1] + 1
        node = 0
        for end in range(start, len(s)):
            node = children[node].get(s[end], -1)
            if node == -1:
                break
            if terminal[node]:
                best[start] = min(best[start], best[end + 1])
    return best[0]


class Solution:
    def minExtraChar(self, s: str, dictionary: list[str]) -> int:
        return solve(s, dictionary)
