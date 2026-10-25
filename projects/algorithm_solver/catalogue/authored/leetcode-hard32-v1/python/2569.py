"""2569. Handling Sum Queries After Update."""

def solve(nums1: list[int], nums2: list[int], queries: list[list[int]]) -> list[int]:
    """O(n+q log n) time, O(n+q) space; lazy range flips plus an exact running sum."""
    size = len(nums1)
    ones = [0] * (4 * size)
    lazy = [False] * (4 * size)

    def build(node: int, left: int, right: int) -> None:
        if left == right:
            ones[node] = nums1[left]
            return
        middle = (left + right) // 2
        build(node * 2, left, middle)
        build(node * 2 + 1, middle + 1, right)
        ones[node] = ones[node * 2] + ones[node * 2 + 1]

    def apply(node: int, length: int) -> None:
        ones[node] = length - ones[node]
        lazy[node] = not lazy[node]

    def flip(node: int, left: int, right: int, start: int, stop: int) -> None:
        if start <= left and right <= stop:
            apply(node, right - left + 1)
            return
        middle = (left + right) // 2
        if lazy[node]:
            apply(node * 2, middle - left + 1)
            apply(node * 2 + 1, right - middle)
            lazy[node] = False
        if start <= middle:
            flip(node * 2, left, middle, start, stop)
        if stop > middle:
            flip(node * 2 + 1, middle + 1, right, start, stop)
        ones[node] = ones[node * 2] + ones[node * 2 + 1]

    build(1, 0, size - 1)
    total = sum(nums2)
    answer = []
    for kind, first, second in queries:
        if kind == 1:
            flip(1, 0, size - 1, first, second)
        elif kind == 2:
            total += first * ones[1]
        else:
            answer.append(total)
    return answer


class Solution:
    def handleQuery(self, nums1: list[int], nums2: list[int], queries: list[list[int]]) -> list[int]:
        return solve(nums1, nums2, queries)
