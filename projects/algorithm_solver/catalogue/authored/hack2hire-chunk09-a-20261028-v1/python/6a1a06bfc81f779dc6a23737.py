"""Hack2Hire 6a1a06bfc81f779dc6a23737 (AI Token Billing Calculation, variant 1 of 3) over an INFERRED spec; qualification unknown."""


def solve(sessions, pricing):
    prices = {}
    for row in pricing:
        plan, inp, outp = row.split(',')
        prices[plan] = (int(inp), int(outp))
    totals = {}
    for row in sessions:
        user, inp, outp, plan = row.split(',')
        pin, pout = prices[plan]
        totals[user] = totals.get(user, 0) + int(inp) * pin + int(outp) * pout
    return [[user, totals[user]] for user in sorted(totals)]


class Solution:
    def calculateMonthlySpend(self, sessions, pricing):
        return solve(sessions, pricing)
