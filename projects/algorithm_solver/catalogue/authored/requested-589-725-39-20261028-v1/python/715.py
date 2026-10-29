"""Original LeetCode 715 candidate; qualification unknown."""

class RangeModule:
    def __init__(self): self.intervals = []
    def addRange(self, left, right):
        out, inserted = [], False
        for a, b in self.intervals:
            if b < left: out.append((a,b))
            elif right < a:
                if not inserted: out.append((left,right)); inserted = True
                out.append((a,b))
            else: left, right = min(left,a), max(right,b)
        if not inserted: out.append((left,right))
        self.intervals = out
    def queryRange(self, left, right):
        for a,b in self.intervals:
            if a <= left and right <= b: return True
            if a > left: return False
        return False
    def removeRange(self, left, right):
        out = []
        for a,b in self.intervals:
            if b <= left or right <= a: out.append((a,b))
            else:
                if a < left: out.append((a,left))
                if right < b: out.append((right,b))
        self.intervals = out


def solve(operations, arguments):
    instance = RangeModule(*arguments[0])
    result = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        result.append(getattr(instance, operation)(*values))
    return result
