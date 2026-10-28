"""2813. Maximum Elegance of a K-Length Subsequence (Hard).

Specification: https://leetcode.com/problems/maximum-elegance-of-a-k-length-subsequence/description/
"""


def solve(items, k):
    sorted_items = sorted(items, key=lambda x: -x[0])
    tot = 0
    seen = set()
    dup = []
    for p, c in sorted_items[:k]:
        tot += p
        if c in seen:
            dup.append(p)
        else:
            seen.add(c)
    ans = tot + len(seen) * len(seen)
    for p, c in sorted_items[k:]:
        if c in seen:
            continue
        if not dup:
            break
        tot += p - dup.pop()
        seen.add(c)
        ans = max(ans, tot + len(seen) * len(seen))
    return ans


class Solution:
    def findMaximumElegance(self, *args):
        return solve(*args)
