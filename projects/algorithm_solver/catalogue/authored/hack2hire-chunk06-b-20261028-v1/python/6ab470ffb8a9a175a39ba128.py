"""Hack2Hire 6ab470ffb8a9a175a39ba128 (Guess Number with Delay, level 2) over an INFERRED spec; qualification unknown."""

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


def solve(upperBound, delay, secret):
    return _search(upperBound, delay, secret)


class Solution:
    def findSecretWithDelay(self, upperBound, delay, secret):
        return solve(upperBound, delay, secret)
