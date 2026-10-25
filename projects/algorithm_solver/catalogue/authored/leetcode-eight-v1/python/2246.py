"""Bottom-up tree paths, without recursion or a parent-before-child assumption."""


def solve(parent: list[int], s: str) -> int:
    """O(n) time and space; handle a depth-100000 tree without recursion."""
    size = len(parent)
    remaining = [0] * size
    for ancestor in parent[1:]:
        remaining[ancestor] += 1
    first, second = [0] * size, [0] * size
    queue = [node for node, count in enumerate(remaining) if count == 0]
    best, head = 1, 0
    while head < len(queue):
        node = queue[head]
        head += 1
        best = max(best, 1 + first[node] + second[node])
        ancestor = parent[node]
        if ancestor == -1:
            continue
        if s[node] != s[ancestor]:
            length = first[node] + 1
            if length > first[ancestor]:
                second[ancestor] = first[ancestor]
                first[ancestor] = length
            elif length > second[ancestor]:
                second[ancestor] = length
        remaining[ancestor] -= 1
        if remaining[ancestor] == 0:
            queue.append(ancestor)
    return best


class Solution:
    def longestPath(self, parent: list[int], s: str) -> int:
        return solve(parent, s)
