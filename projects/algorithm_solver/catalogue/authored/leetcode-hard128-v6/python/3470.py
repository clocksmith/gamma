"""3470. Permutations IV.

Unrank alternating-parity permutations using exact factorial completion counts; O(n^2) arithmetic operations and O(n) space. Inputs are preserved.
"""

def solve(n: int, k: int) -> list[int]:
    factorial = [1]
    for value in range(1, n + 1):
        factorial.append(factorial[-1] * value)
    used = [False] * (n + 1)
    odd, even = (n + 1) // 2, n // 2
    answer = []
    for position in range(n):
        chosen = False
        for value in range(1, n + 1):
            if used[value] or (answer and value % 2 == answer[-1] % 2):
                continue
            remaining_odd = odd - (value % 2)
            remaining_even = even - (1 - value % 2)
            remaining = n - position - 1
            needed_odd = (remaining + (value % 2 == 0)) // 2
            if remaining_odd != needed_odd or remaining_even != remaining - needed_odd:
                continue
            completions = factorial[remaining_odd] * factorial[remaining_even]
            if k > completions:
                k -= completions
                continue
            answer.append(value)
            used[value] = True
            odd, even = remaining_odd, remaining_even
            chosen = True
            break
        if not chosen:
            return []
    return answer


class Solution:
    def permute(self, n: int, k: int) -> list[int]:
        return solve(n, k)
