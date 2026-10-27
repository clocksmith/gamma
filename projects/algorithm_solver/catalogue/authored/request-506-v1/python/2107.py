# Original implementation. Contract: https://leetcode.com/problems/number-of-unique-flavors-after-sharing-k-candies/
from collections import Counter
def solve(candies,k):
    c=Counter(candies[k:]);out=len(c)
    for i in range(k,len(candies)):
        c[candies[i-k]]+=1;c[candies[i]]-=1
        if c[candies[i]]==0:del c[candies[i]]
        out=max(out,len(c))
    return out
