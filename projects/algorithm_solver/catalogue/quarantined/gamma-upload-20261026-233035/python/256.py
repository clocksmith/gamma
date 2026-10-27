"""256. Paint House."""
def solve(costs: list[list[int]]) -> int:
    red = blue = green = 0
    for first, second, third in costs:
        red, blue, green = first + min(blue, green), second + min(red, green), third + min(red, blue)
    return min(red, blue, green)

class Solution:
    def minCost(self, costs: list[list[int]]) -> int:
        return solve(costs)
