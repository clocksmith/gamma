# Original candidate. Contract: https://leetcode.com/problems/pour-water-between-buckets-to-make-water-levels-equal/
def solve(buckets, loss):
    lo,hi=min(buckets),max(buckets);ratio=1-loss/100
    for _ in range(70):
        mid=(lo+hi)/2;net=sum((x-mid)*ratio if x>mid else x-mid for x in buckets)
        if net>=0:lo=mid
        else:hi=mid
    return lo
