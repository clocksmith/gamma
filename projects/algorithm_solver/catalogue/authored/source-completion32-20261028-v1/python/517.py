# 517 — Super Washing Machines. Original implementation; authored candidate, not independently qualified.
def solve(machines):
    total, n = sum(machines), len(machines)
    if total % n:
        return -1
    average, carry, answer = total // n, 0, 0
    for load in machines:
        carry += load - average
        answer = max(answer, abs(carry), load - average)
    return answer

findMinMoves = solve

class Solution:
    findMinMoves = staticmethod(solve)
