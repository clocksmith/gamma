def solve(weight):
    maximum = None
    shipments = 0
    for value in weight:
        if maximum is not None and value < maximum:
            shipments += 1
            maximum = None
        else:
            maximum = value if maximum is None else max(maximum, value)
    return shipments


class Solution:
    def maxBalancedShipments(self, weight):
        return solve(weight)
