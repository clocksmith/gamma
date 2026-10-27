"""517. Super Washing Machines."""

def solve(machines: list[int]) -> int:
    total = sum(machines)
    if total % len(machines):
        return -1
    average = total // len(machines)
    balance = answer = 0
    for value in machines:
        surplus = value - average
        balance += surplus
        answer = max(answer, abs(balance), surplus)
    return answer


class Solution:
    def findMinMoves(self, machines: list[int]) -> int:
        return solve(machines)
