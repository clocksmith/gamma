"""3851. Maximum Requests Without Violating the Limit
Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
Signature: solve(requests, k, window).
Algorithm: Per-user sorted greedy retention with a queue of retained requests in the inclusive window.
Complexity: O(n log n) time; O(n) space.
Numeric semantics: Exact integer arithmetic on the published input bounds; JavaScript Number results remain safe integers.
Mutation: Does not mutate input arrays, rows, strings, or trees.
Interface: Ordered-positional solve; native forwarding name included only when confirmed.
Specification: https://leetcode.com/problems/maximum-requests-without-violating-the-limit/description/
Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3800-3899/3851.Maximum%20Requests%20Without%20Violating%20the%20Limit/README_EN.md
Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
New readable implementations; no third-party source bodies copied verbatim.
No protected tests or private reference implementations used.
Contract note: Duplicate requests count separately. Requests exactly window apart remain in the same closed interval.
"""

def solve(requests, k, window):
    by_user = {}
    for user, time in requests:
        by_user.setdefault(user, []).append(time)
    total = 0
    for times in by_user.values():
        times.sort()
        kept = []
        head = 0
        for time in times:
            while head < len(kept) and time - kept[head] > window:
                head += 1
            if len(kept) - head < k:
                kept.append(time)
                total += 1
    return total


def maxRequests(requests, k, window):
    return solve(requests, k, window)


class Solution:
    def maxRequests(self, requests, k, window):
        return solve(requests, k, window)
