"""600. Non-negative Integers without Consecutive Ones. Binary digit counting with Fibonacci suffix counts, including zero."""

def solve(n: int) -> int:
    length = max(1, n.bit_length())
    counts = [1, 2]
    for _ in range(2, length + 1):
        counts.append(counts[-1] + counts[-2])
    answer = previous = 0
    for bit in range(length - 1, -1, -1):
        if n & (1 << bit):
            answer += counts[bit]
            if previous:
                return answer
            previous = 1
        else:
            previous = 0
    return answer + 1


class Solution:
    def findIntegers(self, n: int) -> int:
        return solve(n)
