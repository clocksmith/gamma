"""Hack2Hire 6973d4f9a0697bac5fdca7ad (Cloud Service Usage Cost, variant 1) over an INFERRED spec; qualification unknown."""

def _scaled(rate):
    whole, _, fraction = rate.partition('.')
    return int(whole) * 10000 + int((fraction + '0000')[:4])  # units of 1e-4 dollars


def _money(units):
    cents = (units + 50) // 100
    return str(cents // 100) + '.' + str(cents % 100).rjust(2, '0')


def solve(usageReport, pricingTable):
    prices = pricingTable.get(usageReport['region'], {})
    total = sum(_scaled(prices[row['service']]) * row['hours'] for row in usageReport['services'] if row['service'] in prices)
    return _money(total)


class Solution:
    def calculateCost(self, usageReport, pricingTable):
        return solve(usageReport, pricingTable)
