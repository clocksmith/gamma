class Solution:
    def findCenter(self, edges: list[list[int]]) -> int:
        first, second = edges[0]
        other_first, other_second = edges[1]
        if first == other_first or first == other_second:
            return first
        return second
