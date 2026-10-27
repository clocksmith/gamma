"""275. H-Index II."""
def solve(citations: list[int]) -> int:
    size = len(citations)
    left, right = 0, size
    while left < right:
        middle = (left + right) // 2
        if citations[middle] >= size - middle:
            right = middle
        else:
            left = middle + 1
    return size - left

class Solution:
    def hIndex(self, citations: list[int]) -> int:
        return solve(citations)
