"""2157. Groups of Strings."""


def solve(words: list[str]) -> list[int]:
    """Union equal masks, deletion neighbors, and shared deletion signatures; O(L+26*n*alpha(n)) time, O(26*n) space. Inputs are preserved."""
    size = len(words)
    parent = list(range(size))
    sizes = [1] * size

    def find(node):
        while node != parent[node]:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    def union(first, second):
        left, right = find(first), find(second)
        if left == right:
            return
        if sizes[left] < sizes[right]:
            left, right = right, left
        parent[right] = left
        sizes[left] += sizes[right]

    masks = []
    owners = {}
    for index, word in enumerate(words):
        mask = 0
        for character in word:
            mask |= 1 << (ord(character) - ord('a'))
        masks.append(mask)
        if mask in owners:
            union(index, owners[mask])
        else:
            owners[mask] = index
    removed_owners = {}
    for index, mask in enumerate(masks):
        bits = mask
        while bits:
            bit = bits & -bits
            bits ^= bit
            removed = mask ^ bit
            if removed in owners:
                union(index, owners[removed])
            if removed in removed_owners:
                union(index, removed_owners[removed])
            else:
                removed_owners[removed] = index
    roots = {find(index) for index in range(size)}
    return [len(roots), max(sizes[root] for root in roots)]


class Solution:
    def groupStrings(self, words: list[str]) -> list[int]:
        return solve(words)
