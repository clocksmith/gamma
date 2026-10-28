"""1850. Minimum Adjacent Swaps to Reach the Kth Smallest Number (Medium).

Specification: https://leetcode.com/problems/minimum-adjacent-swaps-to-reach-the-kth-smallest-number/description/
"""


def _next_permutation(chars):
    i = len(chars) - 2
    while i >= 0 and chars[i] >= chars[i + 1]:
        i -= 1
    if i < 0:
        return False
    j = len(chars) - 1
    while chars[j] <= chars[i]:
        j -= 1
    chars[i], chars[j] = chars[j], chars[i]
    left, right = i + 1, len(chars) - 1
    while left < right:
        chars[left], chars[right] = chars[right], chars[left]
        left += 1
        right -= 1
    return True


def solve(num: str, k: int) -> int:
    target = list(num)
    for _step in range(k):
        _next_permutation(target)
    positions = {}
    for i, digit in enumerate(num):
        positions.setdefault(digit, []).append(i)
    used = {}
    sequence = []
    for digit in target:
        index = used.get(digit, 0)
        sequence.append(positions[digit][index])
        used[digit] = index + 1
    inversions = 0
    for i in range(len(sequence)):
        for j in range(i + 1, len(sequence)):
            if sequence[i] > sequence[j]:
                inversions += 1
    return inversions


class Solution:
    def getMinSwaps(self, num: str, k: int) -> int:
        return solve(num, k)
