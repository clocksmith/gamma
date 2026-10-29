"""Original LeetCode 600 candidate; qualification unknown."""

def solve(n):
    counts = [1, 2]
    for _ in range(2, 31):
        counts.append(counts[-1] + counts[-2])
    answer = previous = 0
    for bit in range(30, -1, -1):
        if n >> bit & 1:
            answer += counts[bit]
            if previous:
                return answer
            previous = 1
        else:
            previous = 0
    return answer + 1


class Solution:
    def findIntegers(self, n):
        return solve(n)
