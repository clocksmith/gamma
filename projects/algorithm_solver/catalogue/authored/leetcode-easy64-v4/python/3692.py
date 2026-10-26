"""3692. Majority Frequency Characters (Easy).

Specification: https://leetcode.com/problems/majority-frequency-characters/description/
"""


def solve(s: str) -> str:
    """O(n) time, O(1) alphabet space; return tied-group characters in alphabetical order."""
    counts = [0] * 26
    for character in s:
        counts[ord(character) - ord('a')] += 1
    groupSizes = {}
    for count in counts:
        if count > 0:
            groupSizes[count] = groupSizes.get(count, 0) + 1
    bestFrequency = 0
    bestSize = 0
    for frequency, size in groupSizes.items():
        if size > bestSize or (size == bestSize and frequency > bestFrequency):
            bestFrequency = frequency
            bestSize = size
    result = []
    for index in range(26):
        if counts[index] == bestFrequency:
            result.append(chr(ord('a') + index))
    return ''.join(result)


class Solution:
    def majorityFrequencyGroup(self, s: str) -> str:
        return solve(s)
