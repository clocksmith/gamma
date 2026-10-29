"""Original frontend 352 variant; qualification unknown."""


class SummaryRanges:
    def __init__(self):
        self.intervals = []

    def addNum(self, value: int) -> None:
        ivs = self.intervals
        low, high = 0, len(ivs)
        while low < high:
            mid = (low + high) // 2
            if ivs[mid][0] <= value:
                low = mid + 1
            else:
                high = mid
        idx = low
        if idx > 0 and ivs[idx - 1][1] >= value:
            return
        left_merge = idx > 0 and ivs[idx - 1][1] + 1 == value
        right_merge = idx < len(ivs) and ivs[idx][0] - 1 == value
        if left_merge and right_merge:
            ivs[idx - 1][1] = ivs[idx][1]
            ivs.pop(idx)
        elif left_merge:
            ivs[idx - 1][1] = value
        elif right_merge:
            ivs[idx][0] = value
        else:
            ivs.insert(idx, [value, value])

    def getIntervals(self):
        return [[a, b] for a, b in self.intervals]


def solve(operation_names, argument_lists):
    instance = SummaryRanges()
    out = [None]
    for op, args in zip(operation_names[1:], argument_lists[1:]):
        if op == "addNum":
            instance.addNum(args[0])
            out.append(None)
        elif op == "getIntervals":
            out.append(instance.getIntervals())
        else:
            raise ValueError("unknown operation")
    return out
