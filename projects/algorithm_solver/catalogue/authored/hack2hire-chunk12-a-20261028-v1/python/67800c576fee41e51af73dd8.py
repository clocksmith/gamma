"""Hack2Hire 67800c576fee41e51af73dd8 (Max Consecutive ON Servers) over an INFERRED spec; qualification unknown."""


def solve(states, k):
    left = blocks = best = 0
    for right, ch in enumerate(states):
        if ch == '0' and (right == left or states[right - 1] == '1'):
            blocks += 1
        while blocks > k:
            if states[left] == '0' and not (left + 1 <= right and states[left + 1] == '0'):
                blocks -= 1
            left += 1
        if right - left + 1 > best:
            best = right - left + 1
    return best


class Solution:
    def maxConsecutiveOn(self, states, k):
        return solve(states, k)
