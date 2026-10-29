"""Hack2Hire 678314d4d0faf7ec64cc3ad6 (Calculate Dasher Salary, variant 1) over an INFERRED spec; qualification unknown."""

RATE_CENTS_PER_MINUTE = 30


def solve(records):
    accepted, delivered = {}, {}
    for order_id, stamp, status in records:
        minute = int(stamp[:2]) * 60 + int(stamp[3:])
        if status == 'ACCEPTED':
            accepted[order_id] = minute
        elif status == 'DELIVERED':
            delivered[order_id] = minute
    return sum(RATE_CENTS_PER_MINUTE * (end - accepted[order_id]) for order_id, end in delivered.items())


class Solution:
    def calculateSalary(self, records):
        return solve(records)
