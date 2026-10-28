"""2534. Time Taken to Cross the Door (Hard).

Specification: https://leetcode.com/problems/time-taken-to-cross-the-door/description/
"""


from collections import deque


def solve(arrival, state):
    n = len(arrival)
    q = [deque(), deque()]
    ans = [0] * n
    t = i = 0
    st = 1
    while i < n or q[0] or q[1]:
        while i < n and arrival[i] <= t:
            q[state[i]].append(i)
            i += 1
        if q[0] and q[1]:
            ans[q[st].popleft()] = t
        elif q[0] or q[1]:
            st = 0 if q[0] else 1
            ans[q[st].popleft()] = t
        else:
            st = 1
        t += 1
    return ans


class Solution:
    def timeTaken(self, arrival, state):
        return solve(arrival, state)
