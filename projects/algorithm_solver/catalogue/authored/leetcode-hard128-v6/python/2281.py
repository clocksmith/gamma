"""2281. Sum of Total Strength of Wizards.

Monotonic minimum boundaries and prefix-of-prefix sums; O(n) time and space. Inputs are preserved; modular products are exact.
"""

def solve(strength: list[int]) -> int:
    modulus = 1_000_000_007
    n = len(strength)
    left, right = [-1] * n, [n] * n
    stack = []
    for index, value in enumerate(strength):
        while stack and strength[stack[-1]] >= value:
            right[stack.pop()] = index
        if stack:
            left[index] = stack[-1]
        stack.append(index)
    prefix = [0]
    for value in strength:
        prefix.append((prefix[-1] + value) % modulus)
    twice = [0]
    for value in prefix:
        twice.append((twice[-1] + value) % modulus)
    answer = 0
    for index, value in enumerate(strength):
        a, b = left[index], right[index]
        total = (index - a) * (twice[b + 1] - twice[index + 1]) - (b - index) * (twice[index + 1] - twice[a + 1])
        answer = (answer + value * total) % modulus
    return answer


class Solution:
    def totalStrength(self, strength: list[int]) -> int:
        return solve(strength)
