"""1439. Find the Kth Smallest Sum of a Matrix With Sorted Rows: merge only the k smallest partial sums; O(rows*k*log(k+1)) time and O(k) space."""

from heapq import heapify, heappop, heappush


def solve(mat: list[list[int]], k: int) -> int:
    partial = [0]
    for row in mat:
        heap = [(value + row[0], index, 0) for index, value in enumerate(partial)]
        heapify(heap)
        following = []
        while heap and len(following) < k:
            value, previous_index, column = heappop(heap)
            following.append(value)
            if column + 1 < len(row):
                heappush(heap, (partial[previous_index] + row[column + 1], previous_index, column + 1))
        partial = following
    return partial[k - 1]


class Solution:
    def kthSmallest(self, mat: list[list[int]], k: int) -> int:
        return solve(mat, k)
