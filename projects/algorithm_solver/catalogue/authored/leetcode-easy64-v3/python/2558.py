"""2558. Take Gifts From the Richest Pile (Easy).

Specification: https://leetcode.com/problems/take-gifts-from-the-richest-pile/description/
"""

from math import isqrt


def solve(gifts: list[int], k: int) -> int:
    """O(n + k log n) time, O(n) space; preserve gifts and maintain a max heap."""
    heap = gifts.copy()

    def sift_down(index: int) -> None:
        value = heap[index]
        while 2 * index + 1 < len(heap):
            child = 2 * index + 1
            if child + 1 < len(heap) and heap[child + 1] > heap[child]:
                child += 1
            if heap[child] <= value:
                break
            heap[index] = heap[child]
            index = child
        heap[index] = value

    for index in range(len(heap) // 2 - 1, -1, -1):
        sift_down(index)
    for _ in range(k):
        if heap[0] <= 1:
            break
        heap[0] = isqrt(heap[0])
        sift_down(0)
    return sum(heap)


class Solution:
    def pickGifts(self, gifts: list[int], k: int) -> int:
        return solve(gifts, k)
