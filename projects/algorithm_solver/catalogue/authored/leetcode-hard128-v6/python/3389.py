"""3389. Minimum Operations to Make Character Frequencies Equal.

Try each final frequency and account for adjacent-letter transfers with alphabet dynamic programming; O(26*n) time and O(26) space. Input is preserved.
"""

def solve(s: str) -> int:
    counts = [0] * 26
    for character in s:
        counts[ord(character) - 97] += 1
    answer = len(s)
    for target in range(1, max(counts) + 1):
        best = [0] * 28
        for index in range(25, -1, -1):
            count = counts[index]
            best[index] = min(count, abs(count - target)) + best[index + 1]
            if index < 25 and counts[index + 1] < target:
                deficit = target - counts[index + 1]
                excess = max(0, count - target)
                keep = abs(count - target) + deficit - min(excess, deficit)
                remove = count + deficit - min(count, deficit)
                best[index] = min(best[index], min(keep, remove) + best[index + 2])
        answer = min(answer, best[0])
    return answer


class Solution:
    def makeStringGood(self, s: str) -> int:
        return solve(s)
