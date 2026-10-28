"""831. Masking Personal Information (Medium).

Specification: https://leetcode.com/problems/masking-personal-information/description/
"""


import re


def solve(s: str) -> str:
    if '@' in s:
        lower = s.lower()
        at = lower.index('@')
        return lower[0] + '*****' + lower[at - 1] + lower[at:]
    digits = re.sub(r'\D', '', s)
    local = digits[-10:]
    country = digits[:-10]
    if country == '':
        return '***-***-' + local[-4:]
    return '+' + '*' * len(country) + '-***-***-' + local[-4:]


class Solution:
    def maskPII(self, s: str) -> str:
        return solve(s)
