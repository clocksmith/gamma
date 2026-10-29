"""Hack2Hire 6784b4640e1dbb6a09385784 (Dasher Payment Model, variant 3) over an INFERRED spec; qualification unknown."""

PEAKS = ((660, 840), (1020, 1200))  # [11:00, 14:00) and [17:00, 20:00), weighted 2


def weighted_before(t):
    total = t
    for start, end in PEAKS:
        if t > start:
            total += min(t, end) - start
    return total


def solve(activities):
    cancelled = {order for _, order, event in activities if event == 'cancelled'}
    count = 0
    paid = 0
    previous = 0
    for time, order, event in activities:
        t = int(time[:2]) * 60 + int(time[3:])
        paid += count * (weighted_before(t) - weighted_before(previous))
        previous = t
        if order in cancelled:
            continue
        count += 1 if event == 'accepted' else -1
    return 30 * paid


class Solution:
    def calculatePay(self, activities):
        return solve(activities)
