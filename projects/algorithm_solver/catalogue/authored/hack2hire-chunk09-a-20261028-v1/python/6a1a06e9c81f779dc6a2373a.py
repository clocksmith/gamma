"""Hack2Hire 6a1a06e9c81f779dc6a2373a (AI Token Billing Calculation, variant 2 of 3) over an INFERRED spec; qualification unknown."""


def solve(sessions, pricing):
    prices = {}
    for row in pricing:
        plan, inp, outp, fee, free = row.split(',')
        prices[plan] = (int(inp), int(outp), int(fee), int(free))
    left = {}
    totals = {}
    for row in sessions:
        user, inp, outp, plan = row.split(',')
        pin, pout, fee, free = prices[plan]
        key = (user, plan)
        charge = 0
        if key not in left:
            left[key] = free
            charge = fee
        remaining = left[key]
        tin, tout = int(inp), int(outp)
        use = tin if tin < remaining else remaining
        remaining -= use
        charge += (tin - use) * pin
        use = tout if tout < remaining else remaining
        remaining -= use
        charge += (tout - use) * pout
        left[key] = remaining
        totals[user] = totals.get(user, 0) + charge
    return [[user, totals[user]] for user in sorted(totals)]


class Solution:
    def calculateMonthlySpend(self, sessions, pricing):
        return solve(sessions, pricing)
