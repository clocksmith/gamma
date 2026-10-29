# 306 — Additive Number. Original implementation; authored candidate, not independently qualified.
def solve(num):
    n = len(num)
    for a in range(1, n - 1):
        if a > 1 and num[0] == '0':
            break
        for b in range(a + 1, n):
            if b - a > 1 and num[a] == '0':
                break
            x, y, pos = int(num[:a]), int(num[a:b]), b
            while pos < n:
                z = x + y
                token = str(z)
                if not num.startswith(token, pos):
                    break
                pos += len(token)
                x, y = y, z
            if pos == n:
                return True
    return False

isAdditiveNumber = solve

class Solution:
    isAdditiveNumber = staticmethod(solve)
