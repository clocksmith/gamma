def solve(balance):
    if sum(balance) < 0:
        return -1
    sink = next((i for i, x in enumerate(balance) if x < 0), None)
    if sink is None:
        return 0
    n = len(balance)
    supply = [0] * (n // 2 + 1)
    for i, value in enumerate(balance):
        if value > 0:
            d = abs(i - sink)
            supply[min(d, n - d)] += value
    need = -balance[sink]
    answer = 0
    for d, available in enumerate(supply):
        take = min(available, need)
        answer += take * d
        need -= take
        if need == 0:
            return answer
    return -1


class Solution:
    def minMoves(self, balance):
        return solve(balance)
