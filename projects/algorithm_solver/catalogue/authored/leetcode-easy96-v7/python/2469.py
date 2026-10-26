"""2469. Convert the Temperature (Easy).

Specification: https://leetcode.com/problems/convert-the-temperature/description/
"""


def solve(celsius: float) -> list[float]:
    """O(1) time and space; return Kelvin then Fahrenheit using the specified binary64 arithmetic."""
    return [celsius + 273.15, celsius * 1.8 + 32.0]


class Solution:
    def convertTemperature(self, celsius: float) -> list[float]:
        return solve(celsius)
