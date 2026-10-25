class Solution:
    def leastBricks(self, wall: list[list[int]]) -> int:
        edges = {}
        aligned = 0
        for row in wall:
            offset = 0
            for index in range(len(row) - 1):
                offset += row[index]
                edges[offset] = edges.get(offset, 0) + 1
                aligned = max(aligned, edges[offset])
        return len(wall) - aligned
