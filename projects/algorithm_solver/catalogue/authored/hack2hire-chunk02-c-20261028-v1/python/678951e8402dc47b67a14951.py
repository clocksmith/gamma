"""Hack2Hire 678951e8402dc47b67a14951 (Currency Exchange, variant 1) over an INFERRED spec; qualification unknown."""

def _scaled(rate):
    whole, _, fraction = rate.partition('.')
    return int(whole) * 10000 + int((fraction + '0000')[:4])  # rate = value / 10**4


def solve(rates, fromCurrency, toCurrency):
    if fromCurrency == toCurrency:
        return '1'
    edges = [(source, target, _scaled(rate)) for source, target, rate in rates]
    currencies = {source for source, _, _ in edges} | {target for _, target, _ in edges}
    best = {fromCurrency: (1, 0)}  # currency -> (numerator, steps) meaning numerator / 10**(4*steps)
    for _ in range(max(0, len(currencies) - 1)):
        changed = False
        for source, target, value in edges:
            if source not in best:
                continue
            numerator, steps = best[source]
            candidate = (numerator * value, steps + 1)
            current = best.get(target)
            if current is None or candidate[0] * 10 ** (4 * current[1]) > current[0] * 10 ** (4 * candidate[1]):
                best[target] = candidate
                changed = True
        if not changed:
            break
    if toCurrency not in best:
        return '-1'
    numerator, steps = best[toCurrency]
    digits = str(numerator).rjust(4 * steps + 1, '0')
    whole, fraction = digits[:len(digits) - 4 * steps], digits[len(digits) - 4 * steps:].rstrip('0')
    return whole + ('.' + fraction if fraction else '')


class Solution:
    def bestExchangeRate(self, rates, fromCurrency, toCurrency):
        return solve(rates, fromCurrency, toCurrency)
