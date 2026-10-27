"""3646. Next Special Palindrome Number.

Specification: https://leetcode.com/problems/next-special-palindrome-number/description/
Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
O(2^9 * digitLength * alphabet^2) time, O(digitLength + alphabet) working space; enumerate digit multisets, not factorial permutations.
Inputs are not modified.
Input n <= 1e15; candidate comparisons use exact integers. The selected successor fits the safe JS integer domain.
"""

def solve(n):
    target = str(n)
    answer = None
    def next_permutation(characters):
        pivot = len(characters) - 2
        while pivot >= 0 and characters[pivot] >= characters[pivot + 1]:
            pivot -= 1
        if pivot < 0:
            return None
        successor = len(characters) - 1
        while characters[successor] <= characters[pivot]:
            successor -= 1
        characters[pivot], characters[successor] = characters[successor], characters[pivot]
        characters[pivot + 1:] = reversed(characters[pivot + 1:])
        return ''.join(characters)
    for subset in range(1, 1 << 9):
        digits = [digit for digit in range(1, 10) if subset & (1 << (digit - 1))]
        length = sum(digits)
        odd = [digit for digit in digits if digit % 2]
        if len(odd) > 1 or length < len(target) or length > len(target) + 1:
            continue
        counts = [0] * 10
        for digit in digits:
            counts[digit] = digit // 2
        center = str(odd[0]) if odd else ''
        half_size = length // 2
        if length > len(target):
            half = ''.join(str(digit) * counts[digit] for digit in range(1, 10))
        else:
            prefix = target[:half_size]
            def at_least(position):
                if position == half_size:
                    return ''
                required = int(prefix[position])
                for digit in range(max(1, required), 10):
                    if counts[digit] == 0:
                        continue
                    counts[digit] -= 1
                    if digit > required:
                        suffix = ''.join(str(other) * counts[other] for other in range(1, 10))
                    else:
                        suffix = at_least(position + 1)
                    counts[digit] += 1
                    if suffix is not None:
                        return str(digit) + suffix
                return None
            half = at_least(0)
            if half is None:
                continue
        candidate = int(half + center + half[::-1])
        if candidate <= n:
            half = next_permutation(list(half))
            if half is None:
                continue
            candidate = int(half + center + half[::-1])
        if answer is None or candidate < answer:
            answer = candidate
    return answer


class Solution:
    def specialPalindrome(self, n):
        return solve(n)
