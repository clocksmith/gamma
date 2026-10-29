"""Hack2Hire 6a1a0a50c81f779dc6a23753 (Credit Card Fraud Detection, variant 1 of 3) over an INFERRED spec; qualification unknown."""


def solve(requests):
    parsed = []
    for s in requests:
        fields = s.split(',')
        parsed.append((int(fields[0]), fields[1]))
    parsed.sort(key=lambda row: row[0])
    return [[uid, 'APPROVE'] for _, uid in parsed]


class Solution:
    def processRequests(self, requests):
        return solve(requests)
