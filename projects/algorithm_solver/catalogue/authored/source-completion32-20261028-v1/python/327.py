# 327 — Count of Range Sum. Original implementation; authored candidate, not independently qualified.
def solve(nums, lower, upper):
    prefix = [0]
    for value in nums:
        prefix.append(prefix[-1] + value)
    scratch = [0] * len(prefix)
    def count(lo, hi):
        if hi - lo <= 1:
            return 0
        mid = (lo + hi) // 2
        answer = count(lo, mid) + count(mid, hi)
        first = last = mid
        for i in range(lo, mid):
            while first < hi and prefix[first] - prefix[i] < lower:
                first += 1
            while last < hi and prefix[last] - prefix[i] <= upper:
                last += 1
            answer += last - first
        i, j = lo, mid
        for k in range(lo, hi):
            if i < mid and (j == hi or prefix[i] <= prefix[j]):
                scratch[k] = prefix[i]
                i += 1
            else:
                scratch[k] = prefix[j]
                j += 1
        prefix[lo:hi] = scratch[lo:hi]
        return answer
    return count(0, len(prefix))

countRangeSum = solve

class Solution:
    countRangeSum = staticmethod(solve)
