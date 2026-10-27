"""423. Reconstruct Original Digits from English."""

from collections import Counter

def solve(s: str) -> str:
    c = Counter(s)
    d = [0] * 10
    d[0], d[2], d[4], d[6], d[8] = c['z'], c['w'], c['u'], c['x'], c['g']
    d[3] = c['h'] - d[8]
    d[5] = c['f'] - d[4]
    d[7] = c['s'] - d[6]
    d[1] = c['o'] - d[0] - d[2] - d[4]
    d[9] = c['i'] - d[5] - d[6] - d[8]
    return ''.join(str(i) * d[i] for i in range(10))


class Solution:
    def originalDigits(self, s: str) -> str:
        return solve(s)
