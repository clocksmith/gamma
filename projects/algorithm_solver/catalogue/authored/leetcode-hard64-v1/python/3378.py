"""3378. Count Connected Components in LCM Graph: union input indices that share a multiple within the threshold."""


def solve(nums: list[int], threshold: int) -> int:
    """O(n + T log T * alpha(n)) time and O(n + T) auxiliary space, T=threshold. Inputs are preserved."""
    n = len(nums)
    parent = list(range(n))
    size = [1] * n
    owner = [-1] * (threshold + 1)
    components = n

    def find(node):
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    for index, value in enumerate(nums):
        if value > threshold:
            continue
        for multiple in range(value, threshold + 1, value):
            if owner[multiple] == -1:
                owner[multiple] = index
            else:
                first = find(index)
                second = find(owner[multiple])
                if first == second:
                    continue
                if size[first] < size[second]:
                    first, second = second, first
                parent[second] = first
                size[first] += size[second]
                components -= 1
    return components


class Solution:
    def countComponents(self, nums: list[int], threshold: int) -> int:
        return solve(nums, threshold)
