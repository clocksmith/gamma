"""2382. Maximum Segment Sum After Removals. Reverse removals and merge active adjacent components."""


def solve(nums: list[int], removeQueries: list[int]) -> list[int]:
    """O(n*alpha(n)) time and O(n) space. Inputs are preserved."""
    size = len(nums)
    parent = list(range(size))
    weight = [1] * size
    totals = [0] * size
    active = [False] * size
    answer = [0] * size

    def find(node):
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    def merge(first, second):
        first, second = find(first), find(second)
        if first == second:
            return first
        if weight[first] < weight[second]:
            first, second = second, first
        parent[second] = first
        weight[first] += weight[second]
        totals[first] += totals[second]
        return first

    largest = 0
    for step in range(size - 1, -1, -1):
        answer[step] = largest
        node = removeQueries[step]
        active[node] = True
        totals[node] = nums[node]
        for neighbor in (node - 1, node + 1):
            if 0 <= neighbor < size and active[neighbor]:
                merge(node, neighbor)
        largest = max(largest, totals[find(node)])
    return answer


class Solution:
    def maximumSegmentSum(self, nums: list[int], removeQueries: list[int]) -> list[int]:
        return solve(nums, removeQueries)
