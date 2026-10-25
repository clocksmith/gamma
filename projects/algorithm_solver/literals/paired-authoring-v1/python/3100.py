class Solution:
    def maxBottlesDrunk(self, numBottles: int, numExchange: int) -> int:
        empty = numBottles
        drunk = numBottles
        required = numExchange
        while empty >= required:
            empty -= required
            required += 1
            empty += 1
            drunk += 1
        return drunk
