class Solution:
    def numberOfPairs(self, nums: list[int]) -> list[int]:
        unmatched = set()
        pairs = 0
        for value in nums:
            if value in unmatched:
                unmatched.remove(value)
                pairs += 1
            else:
                unmatched.add(value)
        return [pairs, len(unmatched)]
