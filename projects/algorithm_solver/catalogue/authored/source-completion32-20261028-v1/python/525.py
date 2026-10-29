# 525 — Contiguous Array. Original implementation; authored candidate, not independently qualified.
def solve(nums):
    first, balance, answer = {0: -1}, 0, 0
    for i, value in enumerate(nums):
        balance += 1 if value == 1 else -1
        if balance in first:
            answer = max(answer, i - first[balance])
        else:
            first[balance] = i
    return answer

findMaxLength = solve

class Solution:
    findMaxLength = staticmethod(solve)
