"""374. Guess Number Higher or Lower."""
def solve(n: int, guess_fn=None) -> int:
    if guess_fn is None:
        guess_fn = globals()['guess']
    left, right = 1, n
    while left <= right:
        middle = (left + right) // 2
        result = guess_fn(middle)
        if result == 0:
            return middle
        if result < 0:
            right = middle - 1
        else:
            left = middle + 1
    return -1

class Solution:
    def guessNumber(self, n: int) -> int:
        return solve(n)
