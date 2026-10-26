"""2081. Sum of k-Mirror Numbers.

Enumerate decimal palindromes in increasing order and check their base-k digits. All results in the declared n<=30 domain fit exact JavaScript integers.
"""

def solve(k: int, n: int) -> int:
    answer = found = 0
    length = 1
    while found < n:
        half_length = (length + 1) // 2
        for half in range(10 ** (half_length - 1), 10 ** half_length):
            prefix = str(half)
            value = int(prefix + (prefix[:-1] if length % 2 else prefix)[::-1])
            remaining = value
            digits = []
            while remaining:
                digits.append(remaining % k)
                remaining //= k
            if digits == digits[::-1]:
                answer += value
                found += 1
                if found == n:
                    return answer
        length += 1
    return answer


class Solution:
    def kMirror(self, k: int, n: int) -> int:
        return solve(k, n)
