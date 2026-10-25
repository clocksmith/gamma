class Solution:
    def distinctDifferenceArray(self, nums: list[int]) -> list[int]:
        remaining = {}
        for value in nums:
            remaining[value] = remaining.get(value, 0) + 1
        prefix = set()
        output = []
        for value in nums:
            remaining[value] -= 1
            if remaining[value] == 0:
                del remaining[value]
            prefix.add(value)
            output.append(len(prefix) - len(remaining))
        return output
