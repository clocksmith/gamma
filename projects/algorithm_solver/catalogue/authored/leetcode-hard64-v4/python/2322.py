"""2322. Minimum Score After Removals on a Tree."""


def solve(nums: list[int], edges: list[list[int]]) -> int:
    """Iterative subtree XORs and ancestor intervals for every cut pair; O(n^2) time and O(n) space. Inputs are preserved."""
    size = len(nums)
    neighbors = [[] for _ in nums]
    for first, second in edges:
        neighbors[first].append(second)
        neighbors[second].append(first)
    entering = [0] * size
    leaving = [0] * size
    subtree = list(nums)
    clock = 0
    stack = [(0, -1, False)]
    while stack:
        node, parent, exiting = stack.pop()
        if exiting:
            leaving[node] = clock
            for child in neighbors[node]:
                if child != parent:
                    subtree[node] ^= subtree[child]
        else:
            entering[node] = clock
            clock += 1
            stack.append((node, parent, True))
            for child in neighbors[node]:
                if child != parent:
                    stack.append((child, node, False))
    total = subtree[0]
    answer = float('inf')
    for first in range(1, size):
        for second in range(first + 1, size):
            if entering[first] <= entering[second] < leaving[first]:
                parts = (subtree[second], subtree[first] ^ subtree[second], total ^ subtree[first])
            elif entering[second] <= entering[first] < leaving[second]:
                parts = (subtree[first], subtree[second] ^ subtree[first], total ^ subtree[second])
            else:
                parts = (subtree[first], subtree[second], total ^ subtree[first] ^ subtree[second])
            answer = min(answer, max(parts) - min(parts))
            if answer == 0:
                return 0
    return answer


class Solution:
    def minimumScore(self, nums: list[int], edges: list[list[int]]) -> int:
        return solve(nums, edges)
