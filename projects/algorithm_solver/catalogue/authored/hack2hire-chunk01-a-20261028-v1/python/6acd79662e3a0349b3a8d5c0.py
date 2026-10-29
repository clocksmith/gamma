"""Hack2Hire 6acd79662e3a0349b3a8d5c0 (Deployment Window Scheduler, variant 2) over an INFERRED spec; qualification unknown."""

WEEK = 10080


def solve(inputCsv):
    allowed, freeze = [0] * (WEEK + 1), [0] * (WEEK + 1)
    for record in inputCsv:
        start, end, kind = record.split(',')
        delta = allowed if kind == 'allowed' else freeze
        delta[int(start)] += 1
        delta[int(end)] -= 1
    result, covered, frozen, open_at = [], 0, 0, None
    for minute in range(WEEK + 1):
        if minute < WEEK:
            covered += allowed[minute]
            frozen += freeze[minute]
        ok = minute < WEEK and covered > 0 and frozen == 0
        if ok and open_at is None:
            open_at = minute
        elif not ok and open_at is not None:
            result.append([open_at, minute])
            open_at = None
    return result


class Solution:
    def deployableWindows(self, inputCsv):
        return solve(inputCsv)
