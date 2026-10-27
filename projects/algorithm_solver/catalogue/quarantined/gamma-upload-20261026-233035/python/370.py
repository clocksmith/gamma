"""370. Range Addition."""
def solve(length: int, updates: list[list[int]]) -> list[int]:
    difference = [0] * (length + 1)
    for start, end, increment in updates:
        difference[start] += increment
        difference[end + 1] -= increment
    result = []
    total = 0
    for index in range(length):
        total += difference[index]
        result.append(total)
    return result

class Solution:
    def getModifiedArray(self, length: int, updates: list[list[int]]) -> list[int]:
        return solve(length, updates)
