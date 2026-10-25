class Solution:
    def maxDistToClosest(self, seats: list[int]) -> int:
        previous = -1
        farthest = 0
        for index, occupied in enumerate(seats):
            if occupied == 0:
                continue
            if previous < 0:
                farthest = index
            else:
                farthest = max(farthest, (index - previous) // 2)
            previous = index
        return max(farthest, len(seats) - 1 - previous)
