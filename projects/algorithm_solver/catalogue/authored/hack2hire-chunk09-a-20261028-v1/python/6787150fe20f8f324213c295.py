"""Hack2Hire 6787150fe20f8f324213c295 (CPU Usage Analysis) over an INFERRED spec; qualification unknown."""


def solve(logs):
    stack, total = [], {}
    previous = None
    for name, action, ts in logs:
        t = int(ts)
        if stack:
            total[stack[-1]] += t - previous
        previous = t
        if action == 'enter':
            stack.append(name)
            total.setdefault(name, 0)
        else:
            stack.pop()
    return [[name, total[name]] for name in sorted(total)]


class Solution:
    def exclusiveTimes(self, logs):
        return solve(logs)
