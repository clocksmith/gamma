"""636. Exclusive Time of Functions (Medium).

Specification: https://leetcode.com/problems/exclusive-time-of-functions/description/
"""


def solve(n: int, logs: list[str]) -> list[int]:
    result = [0] * n
    stack = []
    previous = 0
    for log in logs:
        id_text, kind, time_text = log.split(':')
        ident = int(id_text)
        time = int(time_text)
        if kind == 'start':
            if stack:
                result[stack[-1]] += time - previous
            stack.append(ident)
            previous = time
        else:
            finished = stack.pop()
            result[finished] += time - previous + 1
            previous = time + 1
    return result


class Solution:
    def exclusiveTime(self, n: int, logs: list[str]) -> list[int]:
        return solve(n, logs)
