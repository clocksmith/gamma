"""412. Fizz Buzz (Easy).

Specification: https://leetcode.com/problems/fizz-buzz/description/
"""


def solve(n: int) -> list[str]:
    """O(n log n) character output in general; fresh output strings for integers 1 through n."""
    result = []
    for value in range(1, n + 1):
        word = ''
        if value % 3 == 0:
            word += 'Fizz'
        if value % 5 == 0:
            word += 'Buzz'
        result.append(word or str(value))
    return result


class Solution:
    def fizzBuzz(self, n: int) -> list[str]:
        return solve(n)
