class Solution:
    def numJewelsInStones(self, jewels: str, stones: str) -> int:
        kinds = set(jewels)
        count = 0
        for stone in stones:
            if stone in kinds:
                count += 1
        return count
