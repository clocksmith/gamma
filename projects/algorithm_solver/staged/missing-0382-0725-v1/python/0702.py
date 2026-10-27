"""702. Search in a Sorted Array of Unknown Size. Use the supplied ArrayReader.get API and its out-of-range sentinel, without requiring a length."""

def solve(reader, target):
    low, high = 0, 1
    while reader.get(high) < target:
        low = high + 1
        high *= 2
    while low <= high:
        middle = (low + high) // 2
        value = reader.get(middle)
        if value == target:
            return middle
        if value < target:
            low = middle + 1
        else:
            high = middle - 1
    return -1


class Solution:
    def search(self, reader, target):
        return solve(reader, target)
