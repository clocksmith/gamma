"""274. H-Index."""
def solve(citations: list[int]) -> int:
    citations = sorted(citations, reverse=True)
    answer = 0
    for index, value in enumerate(citations, 1):
        if value < index:
            break
        answer = index
    return answer

class Solution:
    def hIndex(self, citations: list[int]) -> int:
        return solve(citations)
