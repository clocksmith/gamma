"""Hack2Hire 68094bed31dc778b35c5d171 (Violation Log Analyzer) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

from bisect import bisect_left, bisect_right


class ViolationLogAnalyzer:
    def __init__(self, logs):
        self.dates = [log[2] for log in logs]
        self.pairs = [(log[0], log[1]) for log in logs]
        self.by_post = {}
        self.by_policy = {}
        for post, policy, date in logs:
            group = self.by_post.setdefault(post, ([], []))
            group[0].append(date)
            group[1].append(policy)
            group = self.by_policy.setdefault(policy, ([], []))
            group[0].append(date)
            group[1].append(post)

    @staticmethod
    def _distinct(dates, keys, start, end):
        if start > end:
            return 0
        lo = bisect_left(dates, start)
        hi = bisect_right(dates, end)
        return len(set(keys[lo:hi]))

    def countPolicies(self, postId, startDate, endDate):
        group = self.by_post.get(postId)
        return 0 if group is None else self._distinct(group[0], group[1], startDate, endDate)

    def countPosts(self, policy, startDate, endDate):
        group = self.by_policy.get(policy)
        return 0 if group is None else self._distinct(group[0], group[1], startDate, endDate)

    def countViolations(self, startDate, endDate):
        return self._distinct(self.dates, self.pairs, startDate, endDate)


def solve(operation_names, argument_lists):
    if operation_names[0] != 'ViolationLogAnalyzer' or len(argument_lists[0]) != 1:
        raise ValueError('exact initial constructor required')
    instance = ViolationLogAnalyzer(*argument_lists[0])
    allowed = {'countPolicies', 'countPosts', 'countViolations'}
    voids = set()
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
