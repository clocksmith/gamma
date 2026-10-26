"""2736. Maximum Sum Queries. Offline descending first coordinates with a reversed-coordinate Fenwick maximum."""

from bisect import bisect_left


def solve(nums1: list[int], nums2: list[int], queries: list[list[int]]) -> list[int]:
    """O((n+q) log(n+q)) time and O(n+q) space. Inputs are preserved."""
    points = sorted(zip(nums1, nums2), reverse=True)
    coordinates = sorted(set(nums2))
    size = len(coordinates)
    tree = [-1] * (size + 1)
    answer = [-1] * len(queries)
    order = sorted(range(len(queries)), key=lambda index: queries[index][0], reverse=True)
    used = 0
    for index in order:
        minimum_first, minimum_second = queries[index]
        while used < len(points) and points[used][0] >= minimum_first:
            first, second = points[used]
            position = size - bisect_left(coordinates, second)
            value = first + second
            while position <= size:
                tree[position] = max(tree[position], value)
                position += position & -position
            used += 1
        position = size - bisect_left(coordinates, minimum_second)
        best = -1
        while position > 0:
            best = max(best, tree[position])
            position -= position & -position
        answer[index] = best
    return answer


class Solution:
    def maximumSumQueries(self, nums1: list[int], nums2: list[int], queries: list[list[int]]) -> list[int]:
        return solve(nums1, nums2, queries)
