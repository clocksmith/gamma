"""Original hack2hire:68377035587136177f847c00; inferred public-preview contract; qualification unknown."""
from bisect import bisect_right

class AccessSystem:
    def __init__(self, parents):
        children = {name: [] for name in parents}
        root = None
        for name, parent in parents.items():
            if parent is None:
                root = name
            else:
                children[parent].append(name)
        self.bounds = {}
        counter = 0
        stack = [(root, False)]
        while stack:
            name, leaving = stack.pop()
            if leaving:
                self.bounds[name][1] = counter
            else:
                self.bounds[name] = [counter, None]
                counter += 1
                stack.append((name, True))
                for child in reversed(children[name]):
                    stack.append((child, False))
        self.allowed = {}

    def grant(self, advertiser, region):
        intervals = sorted(self.allowed.get(advertiser, []) + [tuple(self.bounds[region])])
        merged = []
        for left, right in intervals:
            if merged and left <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], right))
            else:
                merged.append((left, right))
        self.allowed[advertiser] = merged

    def revoke(self, advertiser, region):
        low, high = self.bounds[region]
        result = []
        for left, right in self.allowed.get(advertiser, []):
            if right <= low or high <= left:
                result.append((left, right))
            else:
                if left < low:
                    result.append((left, low))
                if high < right:
                    result.append((high, right))
        self.allowed[advertiser] = result

    def canAccess(self, advertiser, region):
        position = self.bounds[region][0]
        intervals = self.allowed.get(advertiser, [])
        index = bisect_right(intervals, (position, float('inf'))) - 1
        return index >= 0 and position < intervals[index][1]

def solve(operation_names, argument_lists):
    if len(operation_names) != len(argument_lists) or not operation_names or operation_names[0] != 'AccessSystem':
        raise ValueError("exact constructor trace required")
    instance = AccessSystem(*argument_lists[0])
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in ('grant', 'revoke', 'canAccess'):
            raise ValueError("unknown method")
        result.append(getattr(instance, name)(*arguments))
    return result
