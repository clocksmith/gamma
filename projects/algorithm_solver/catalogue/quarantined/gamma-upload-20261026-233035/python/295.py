"""295. Find Median from Data Stream."""
import heapq

class MedianFinder:
    def __init__(self):
        self.lower = []
        self.upper = []

    def addNum(self, num: int) -> None:
        heapq.heappush(self.lower, -num)
        heapq.heappush(self.upper, -heapq.heappop(self.lower))
        if len(self.upper) > len(self.lower):
            heapq.heappush(self.lower, -heapq.heappop(self.upper))

    def findMedian(self) -> float:
        if len(self.lower) > len(self.upper):
            return float(-self.lower[0])
        return (-self.lower[0] + self.upper[0]) / 2

def solve(operations: list[str], arguments: list[list[int]]) -> list:
    finder = MedianFinder()
    result = []
    for operation, values in zip(operations, arguments):
        if operation == 'MedianFinder':
            result.append(None)
        else:
            result.append(getattr(finder, operation)(*values))
    return result
