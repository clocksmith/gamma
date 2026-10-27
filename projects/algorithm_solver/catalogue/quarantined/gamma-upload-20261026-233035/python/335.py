"""335. Self Crossing."""
def solve(distance: list[int]) -> bool:
    values = distance
    for index in range(3, len(values)):
        if values[index] >= values[index - 2] and values[index - 1] <= values[index - 3]:
            return True
        if index >= 4 and values[index - 1] == values[index - 3] and values[index] + values[index - 4] >= values[index - 2]:
            return True
        if (index >= 5 and values[index - 2] >= values[index - 4]
                and values[index] + values[index - 4] >= values[index - 2]
                and values[index - 1] <= values[index - 3]
                and values[index - 1] + values[index - 5] >= values[index - 3]):
            return True
    return False

class Solution:
    def isSelfCrossing(self, distance: list[int]) -> bool:
        return solve(distance)
