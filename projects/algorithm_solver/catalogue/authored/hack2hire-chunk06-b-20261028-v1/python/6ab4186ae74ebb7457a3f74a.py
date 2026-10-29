"""Hack2Hire 6ab4186ae74ebb7457a3f74a (Guess Number with Delay, level 1) over an INFERRED spec; qualification unknown."""

def _search(upper_bound, delay, secret):
    pending = []  # guesses whose feedback has not been returned yet, oldest first
    calls = 0

    def check(guess):
        nonlocal calls
        calls += 1
        pending.append(guess)
        if len(pending) <= delay:
            return 'PENDING'
        old = pending.pop(0)
        return 'CORRECT' if old == secret else 'TOO_LOW' if old < secret else 'TOO_HIGH'

    lo, hi = 1, upper_bound
    while True:
        mid = (lo + hi) // 2
        for _ in range(delay + 1):
            answer = check(mid)
        if answer == 'CORRECT':
            return [mid, calls]
        if answer == 'TOO_LOW':
            lo = mid + 1
        else:
            hi = mid - 1


def solve(upperBound, secret):
    return _search(upperBound, 1, secret)


class Solution:
    def findSecret(self, upperBound, secret):
        return solve(upperBound, secret)
