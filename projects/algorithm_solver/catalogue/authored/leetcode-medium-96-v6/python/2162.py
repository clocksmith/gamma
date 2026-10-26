"""2162. Minimum Cost to Set Cooking Time: compare both legal minute-second encodings after omitting unnecessary leading zeros."""


def solve(startAt: int, moveCost: int, pushCost: int, targetSeconds: int) -> int:
    """O(1) time and O(1) auxiliary space on the four-digit keypad domain; inputs are read-only."""
    minutes, seconds = divmod(targetSeconds, 60)
    best = float('inf')
    for minute, second in ((minutes, seconds), (minutes - 1, seconds + 60)):
        if not (0 <= minute <= 99 and 0 <= second <= 99):
            continue
        digits = str(minute * 100 + second)
        position = startAt
        cost = 0
        for character in digits:
            digit = ord(character) - ord('0')
            if digit != position:
                cost += moveCost
            cost += pushCost
            position = digit
        best = min(best, cost)
    return int(best)


class Solution:
    def minCostSetTime(self, startAt: int, moveCost: int, pushCost: int, targetSeconds: int) -> int:
        return solve(startAt, moveCost, pushCost, targetSeconds)
