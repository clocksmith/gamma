"""3638. Maximum Balanced Shipments.

Specification: https://leetcode.com/problems/maximum-balanced-shipments/description/
Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
O(n) time, O(1) space; greedily end each shipment at its first strict drop below its maximum.
Inputs are not modified.
"""

def solve(weight):
    maximum = -float('inf')
    answer = 0
    for value in weight:
        if value < maximum:
            answer += 1
            maximum = -float('inf')
        else:
            maximum = value
    return answer


class Solution:
    def maxBalancedShipments(self, weight):
        return solve(weight)
