"""2003. Smallest Missing Genetic Value in Each Subtree.

Only ancestors of value 1 can differ from 1; visit each newly exposed subtree once. O(n) expected time and space. Inputs are preserved.
"""

def solve(parents: list[int], nums: list[int]) -> list[int]:
    answer = [1] * len(nums)
    if 1 not in nums:
        return answer
    children = [[] for _ in nums]
    for node, parent in enumerate(parents):
        if parent != -1:
            children[parent].append(node)
    visited = [False] * len(nums)
    values = set()
    missing = 1
    node = nums.index(1)
    while node != -1:
        stack = [node]
        while stack:
            current = stack.pop()
            if visited[current]:
                continue
            visited[current] = True
            values.add(nums[current])
            stack.extend(children[current])
        while missing in values:
            missing += 1
        answer[node] = missing
        node = parents[node]
    return answer


class Solution:
    def smallestMissingValueSubtree(self, parents: list[int], nums: list[int]) -> list[int]:
        return solve(parents, nums)
