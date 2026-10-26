"""3333. Find the Original Typed String II: subtract short originals using bounded-choice prefix-sum dynamic programming."""


def solve(word: str, k: int) -> int:
    """O(n + k^2) time and O(n + k) auxiliary space. Inputs are preserved."""
    modulus = 1_000_000_007
    runs = []
    length = 0
    previous = ''
    for character in word:
        if character == previous:
            length += 1
        else:
            if length:
                runs.append(length)
            length = 1
            previous = character
    runs.append(length)
    total = 1
    for length in runs:
        total = total * length % modulus
    if len(runs) >= k:
        return total
    ways = [0] * k
    ways[0] = 1
    for length in runs:
        following = [0] * k
        window = 0
        for size in range(1, k):
            window += ways[size - 1]
            if size - length - 1 >= 0:
                window -= ways[size - length - 1]
            window %= modulus
            following[size] = window
        ways = following
    return (total - sum(ways)) % modulus


class Solution:
    def possibleStringCount(self, word: str, k: int) -> int:
        return solve(word, k)
