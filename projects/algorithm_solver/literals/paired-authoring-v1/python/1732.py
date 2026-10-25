class Solution:
    def largestAltitude(self, gain: list[int]) -> int:
        altitude = 0
        highest = 0
        for change in gain:
            altitude += change
            highest = max(highest, altitude)
        return highest
