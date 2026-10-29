"""Hack2Hire 6acd79422e3a0349b3a8d5be (Deployment Window Scheduler, variant 1) over an INFERRED spec; qualification unknown."""

WEEK = 10080


def solve(inputCsv):
    allowed, freeze = [0] * (WEEK + 1), [0] * (WEEK + 1)
    for record in inputCsv:
        start, end, kind = record.split(',')
        delta = allowed if kind == 'allowed' else freeze
        delta[int(start)] += 1
        delta[int(end)] -= 1
    total = covered = frozen = 0
    for minute in range(WEEK):
        covered += allowed[minute]
        frozen += freeze[minute]
        if covered > 0 and frozen == 0:
            total += 1
    return total


class Solution:
    def deployableMinutes(self, inputCsv):
        return solve(inputCsv)
