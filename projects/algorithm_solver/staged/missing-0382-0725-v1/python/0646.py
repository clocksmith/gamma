"""646. Maximum Length of Pair Chain."""

def solve(pairs: list[list[int]]) -> int:
    end = float('-inf')
    answer = 0
    for left, right in sorted(pairs, key=lambda pair: pair[1]):
        if left > end:
            answer += 1
            end = right
    return answer


class Solution:
    def findLongestChain(self, pairs: list[list[int]]) -> int:
        return solve(pairs)
