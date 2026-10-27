# Original implementation. Contract: https://leetcode.com/problems/count-the-number-of-k-free-subsets/
from collections import defaultdict
def solve(nums,k):
    groups=defaultdict(list)
    for x in nums:groups[x%k].append(x)
    out=1
    for group in groups.values():
        skip,take=1,0;previous=None
        for x in sorted(group):
            total=skip+take;take=skip if previous is not None and x-previous==k else total;skip=total;previous=x
        out*=skip+take
    return out
