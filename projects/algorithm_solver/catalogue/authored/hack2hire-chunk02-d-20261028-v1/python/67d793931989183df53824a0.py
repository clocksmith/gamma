"""Hack2Hire 67d793931989183df53824a0 (Fractional Inventory) over an INFERRED spec; qualification unknown."""


def _hundredths(text):
    whole, _, frac = text.partition('.')
    return int(whole) * 100 + int((frac + '00')[:2])


def solve(orders, inventory):
    held = {symbol: int(amount) for symbol, amount in inventory}
    for symbol, kind, quantity, price in orders:
        if quantity[0] == '$':
            amount = _hundredths(quantity[1:]) * 100 // int(price)
        else:
            amount = _hundredths(quantity)
        have = held.get(symbol, 0)
        if kind == 'B':
            if have < amount:
                have += -(-(amount - have) // 100) * 100
            have -= amount
        else:
            have = (have + amount) % 100
        held[symbol] = have
    return [[symbol, str(held[symbol])] for symbol in sorted(held)]


class Solution:
    def fractionalInventory(self, orders, inventory):
        return solve(orders, inventory)
