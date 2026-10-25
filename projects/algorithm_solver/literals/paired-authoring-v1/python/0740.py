class Solution:
    def deleteAndEarn(self, nums: list[int]) -> int:
        points = {}
        for value in nums:
            points[value] = points.get(value, 0) + value
        ordered = sorted(points)
        take = 0
        skip = 0
        previous = None
        for value in ordered:
            best = max(take, skip)
            if previous is not None and value == previous + 1:
                take = skip + points[value]
            else:
                take = best + points[value]
            skip = best
            previous = value
        return max(take, skip)
