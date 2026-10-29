"""Original Hack2Hire 6a4fb137665efda9311f561b variant over an INFERRED specification; qualification unknown."""


def solve(records, percentile):
    counts = {}
    for record in records:
        price, count = record.split(',')
        counts[int(price)] = counts.get(int(price), 0) + int(count)
    need = percentile * sum(counts.values())
    running = 0
    for price in sorted(counts):
        running += counts[price]
        if running * 100 >= need:
            return price
    return -1


class Solution:
    def priceAtPercentile(self, records, percentile):
        return solve(records, percentile)
