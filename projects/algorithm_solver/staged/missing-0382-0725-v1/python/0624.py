"""624. Maximum Distance in Arrays. Compare each array against extrema from previous arrays only."""

def solve(arrays: list[list[int]]) -> int:
    minimum, maximum = arrays[0][0], arrays[0][-1]
    answer = 0
    for row in arrays[1:]:
        answer = max(answer, abs(row[-1] - minimum), abs(maximum - row[0]))
        minimum = min(minimum, row[0])
        maximum = max(maximum, row[-1])
    return answer


class Solution:
    def maxDistance(self, arrays: list[list[int]]) -> int:
        return solve(arrays)
