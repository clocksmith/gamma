"""Original frontend 732 native class variant with a separately declared trace adapter; qualification unknown."""


class MyCalendarThree:
    LIMIT = 10**9

    def __init__(self):
        # Node 0 is the absent child (maximum 0); node 1 covers [0, LIMIT).
        self.left = [0, 0]
        self.right = [0, 0]
        self.added = [0, 0]
        self.best = [0, 0]

    def _child(self):
        self.left.append(0)
        self.right.append(0)
        self.added.append(0)
        self.best.append(0)
        return len(self.best) - 1

    def _update(self, node, low, high, start, end):
        if start <= low and high <= end:
            self.added[node] += 1
            self.best[node] += 1
            return
        middle = (low + high) // 2
        if start < middle:
            if not self.left[node]:
                self.left[node] = self._child()
            self._update(self.left[node], low, middle, start, end)
        if end > middle:
            if not self.right[node]:
                self.right[node] = self._child()
            self._update(self.right[node], middle, high, start, end)
        self.best[node] = self.added[node] + max(self.best[self.left[node]], self.best[self.right[node]])

    def book(self, startTime, endTime):
        self._update(1, 0, self.LIMIT, startTime, endTime)
        return self.best[1]


def solve(operation_names, argument_lists):
    if operation_names[0] != 'MyCalendarThree' or argument_lists[0] != []:
        raise ValueError('exact initial constructor required')
    instance = MyCalendarThree()
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name != 'book':
            raise ValueError('unknown method')
        result.append(instance.book(*arguments))
    return result
