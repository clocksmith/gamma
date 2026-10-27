"""484. Find Permutation. Reverse exactly the maximal descending runs in the initial increasing permutation."""

def solve(s: str) -> list[int]:
    answer = list(range(1, len(s) + 2))
    i = 0
    while i < len(s):
        if s[i] == 'I':
            i += 1
            continue
        j = i
        while j < len(s) and s[j] == 'D':
            j += 1
        answer[i:j + 1] = reversed(answer[i:j + 1])
        i = j
    return answer


class Solution:
    def findPermutation(self, s: str) -> list[int]:
        return solve(s)
