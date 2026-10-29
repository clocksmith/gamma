"""Hack2Hire 67cd196d3363b83a81fc99a7 (Portfolio Value Optimization) over an INFERRED spec; qualification unknown."""


SCALE = 10 ** 8  # distinct ratios S/P (P <= 1e4) differ by >= 1e-8, so floor(S * SCALE / P) orders them exactly and ties only equal ratios


def solve(securities, funds):
    groups = {}
    for _, p, s, a in securities:
        key = s * SCALE // p
        g = groups.get(key)
        if g is None:
            groups[key] = [p * a, s * a, p, s]
        else:
            g[0] += p * a
            g[1] += s * a
    remaining = funds
    whole = 0
    partial_num = 0
    partial_den = 1
    for key in sorted(groups, reverse=True):
        cost, value, p, s = groups[key]
        if cost <= remaining:
            remaining -= cost
            whole += value
        else:
            partial_num = remaining * s
            partial_den = p
            break
    cents = whole * 100 + (200 * partial_num + partial_den) // (2 * partial_den)
    return str(cents // 100) + '.' + str(cents % 100).rjust(2, '0')


class Solution:
    def maximizePortfolioValue(self, securities, funds):
        return solve(securities, funds)
