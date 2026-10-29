"""Hack2Hire 6a1a0712c81f779dc6a2373b (AI Token Billing Calculation, variant 3 of 3) over an INFERRED spec; qualification unknown."""


def solve(sessions, pricing):
    prices = {}
    for row in pricing:
        plan, inp, outp, fee, free, cap = row.split(',')
        prices[plan] = (int(inp), int(outp), int(fee), int(free), int(cap))
    pairs = {}  # (user, plan) -> [remaining free tokens, uncapped usage]
    for row in sessions:
        user, inp, outp, plan = row.split(',')
        pin, pout = prices[plan][0], prices[plan][1]
        key = (user, plan)
        state = pairs.get(key)
        if state is None:
            state = [prices[plan][3], 0]
            pairs[key] = state
        tin, tout = int(inp), int(outp)
        use = tin if tin < state[0] else state[0]
        state[0] -= use
        state[1] += (tin - use) * pin
        use = tout if tout < state[0] else state[0]
        state[0] -= use
        state[1] += (tout - use) * pout
    totals = {}
    for (user, plan), state in pairs.items():
        fee, cap = prices[plan][2], prices[plan][4]
        totals[user] = totals.get(user, 0) + fee + (state[1] if state[1] < cap else cap)
    return [[user, totals[user]] for user in sorted(totals)]


class Solution:
    def calculateMonthlySpend(self, sessions, pricing):
        return solve(sessions, pricing)
