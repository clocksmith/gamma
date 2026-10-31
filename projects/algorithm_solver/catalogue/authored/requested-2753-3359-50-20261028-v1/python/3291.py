"""Original frontend 3291 variant; qualification unknown."""


def solve(words, target: str) -> int:
    trie = {}
    for w in words:
        node = trie
        for ch in w:
            node = node.setdefault(ch, {})
    n = len(target)
    max_reach = [0] * n
    for i in range(n):
        node = trie
        j = i
        while j < n and target[j] in node:
            node = node[target[j]]
            j += 1
        max_reach[i] = j - i
    steps = 0
    cur_end = 0
    farthest = 0
    for i in range(n):
        if i > farthest:
            return -1
        if i + max_reach[i] > farthest:
            farthest = i + max_reach[i]
        if i == cur_end:
            steps += 1
            cur_end = farthest
            if cur_end >= n:
                return steps
    return steps if cur_end >= n else -1


minValidStrings = solve


class Solution:
    def minValidStrings(self, words, target: str) -> int:
        return solve(words, target)
