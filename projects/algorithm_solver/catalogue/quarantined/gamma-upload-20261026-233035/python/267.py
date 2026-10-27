"""267. Palindrome Permutation II."""
from collections import Counter

def solve(s: str) -> list[str]:
    counts = Counter(s)
    middle = ''.join(char for char, count in counts.items() if count % 2)
    if len(middle) > 1:
        return []
    half = []
    for char, count in counts.items():
        half.extend([char] * (count // 2))
    half.sort()
    result = []
    used = [False] * len(half)
    path = []
    def visit() -> None:
        if len(path) == len(half):
            left = ''.join(path)
            result.append(left + middle + left[::-1])
            return
        for index, char in enumerate(half):
            if used[index] or index > 0 and half[index - 1] == char and not used[index - 1]:
                continue
            used[index] = True
            path.append(char)
            visit()
            path.pop()
            used[index] = False
    visit()
    return result

class Solution:
    def generatePalindromes(self, s: str) -> list[str]:
        return solve(s)
