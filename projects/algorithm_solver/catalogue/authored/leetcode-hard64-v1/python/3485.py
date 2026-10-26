"""3485. Longest Common Prefix of K Strings After Removal: count qualified trie prefixes by depth and retract only uniquely fragile depths."""


def solve(words: list[str], k: int) -> list[int]:
    """O(S + n) expected time and O(S + n) space, S=total word length. Inputs are preserved."""
    n = len(words)
    if n - 1 < k:
        return [0] * n
    children = [{}]
    count = [0]
    depth = [0]
    for word in words:
        node = 0
        for character in word:
            if character not in children[node]:
                children[node][character] = len(children)
                children.append({})
                count.append(0)
                depth.append(depth[node] + 1)
            node = children[node][character]
            count[node] += 1
    maximum_depth = max(depth)
    qualified = [0] * (maximum_depth + 1)
    best = 0
    for node in range(1, len(children)):
        if count[node] >= k:
            qualified[depth[node]] += 1
            best = max(best, depth[node])
    answer = []
    for word in words:
        fragile = set()
        node = 0
        for character in word:
            node = children[node][character]
            if count[node] == k and qualified[depth[node]] == 1:
                fragile.add(depth[node])
        result = best
        while result in fragile:
            result -= 1
        answer.append(result)
    return answer


class Solution:
    def longestCommonPrefix(self, words: list[str], k: int) -> list[int]:
        return solve(words, k)
