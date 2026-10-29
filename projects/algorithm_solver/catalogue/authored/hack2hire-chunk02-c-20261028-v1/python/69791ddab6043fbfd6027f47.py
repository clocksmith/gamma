"""Hack2Hire 69791ddab6043fbfd6027f47 (Cloud Service Usage Cost, variant 2) over an INFERRED spec; qualification unknown."""

def _scaled(rate):
    whole, _, fraction = rate.partition('.')
    return int(whole) * 10000 + int((fraction + '0000')[:4])  # units of 1e-4 dollars


def _money(units):
    cents = (units + 50) // 100
    return str(cents // 100) + '.' + str(cents % 100).rjust(2, '0')


def _service_cost(rate, hours):
    if isinstance(rate, str):
        return _scaled(rate) * hours
    cost, charged = 0, 0
    for limit, tier_rate in rate:
        upto = hours if limit is None else min(limit, hours)
        if upto > charged:
            cost += (upto - charged) * _scaled(tier_rate)
            charged = upto
        if charged >= hours:
            break
    return cost


def _costs(usageReport, pricingTable):
    prices = pricingTable.get(usageReport['region'], {})
    hours = {}
    for row in usageReport['services']:
        if row['service'] in prices:
            hours[row['service']] = hours.get(row['service'], 0) + row['hours']
    return {name: _service_cost(prices[name], total) for name, total in hours.items()}


def solve(usageReport, pricingTable):
    return _money(sum(_costs(usageReport, pricingTable).values()))


class Solution:
    def calculateCost(self, usageReport, pricingTable):
        return solve(usageReport, pricingTable)
