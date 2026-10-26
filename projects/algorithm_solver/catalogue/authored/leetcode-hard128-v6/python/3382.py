"""3382. Maximum Area Rectangle With Point Constraints II.

Sweep columns, pair adjacent heights, and query the latest intervening x-coordinate; O(n log n) time and O(n) space. Areas fit exactly below 2^53. Inputs are preserved.
"""

def solve(xCoord: list[int], yCoord: list[int]) -> int:
    points = sorted(zip(xCoord, yCoord))
    heights = sorted(set(yCoord))
    rank = {value: index for index, value in enumerate(heights)}
    size = 1
    while size < len(heights):
        size *= 2
    latest = [-1] * (2 * size)

    def update(index, value):
        index += size
        latest[index] = value
        index //= 2
        while index:
            latest[index] = max(latest[2 * index], latest[2 * index + 1])
            index //= 2

    def maximum(left, right):
        left += size
        right += size + 1
        answer = -1
        while left < right:
            if left & 1:
                answer = max(answer, latest[left])
                left += 1
            if right & 1:
                right -= 1
                answer = max(answer, latest[right])
            left //= 2
            right //= 2
        return answer

    previous = {}
    answer = -1
    start = 0
    while start < len(points):
        end = start + 1
        x = points[start][0]
        while end < len(points) and points[end][0] == x:
            end += 1
        for index in range(start + 1, end):
            bottom, top = points[index - 1][1], points[index][1]
            pair = (bottom, top)
            old = previous.get(pair)
            if old is not None and maximum(rank[bottom], rank[top]) == old:
                answer = max(answer, (x - old) * (top - bottom))
            previous[pair] = x
        for index in range(start, end):
            update(rank[points[index][1]], x)
        start = end
    return answer


class Solution:
    def maxRectangleArea(self, xCoord: list[int], yCoord: list[int]) -> int:
        return solve(xCoord, yCoord)
