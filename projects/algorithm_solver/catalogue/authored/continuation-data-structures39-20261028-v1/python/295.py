"""Original frontend 295 variant; qualification unknown."""
import heapq


class MedianFinder:
    def __init__(self):
        self.lower = []
        self.upper = []

    def addNum(self, num: int) -> None:
        heapq.heappush(self.lower, -int(num))
        heapq.heappush(self.upper, -heapq.heappop(self.lower))
        if len(self.upper) > len(self.lower):
            heapq.heappush(self.lower, -heapq.heappop(self.upper))

    def findMedian(self) -> float:
        if len(self.lower) > len(self.upper):
            return float(-self.lower[0])
        return (-self.lower[0] + self.upper[0]) / 2.0


def solve(operation_names, argument_lists):
    instance = MedianFinder()
    out = [None]
    for op, args in zip(operation_names[1:], argument_lists[1:]):
        if op == "addNum":
            instance.addNum(args[0])
            out.append(None)
        elif op == "findMedian":
            out.append(instance.findMedian())
        else:
            raise ValueError("unknown operation")
    return out
