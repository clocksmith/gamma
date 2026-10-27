# Original implementation. Contract: https://leetcode.com/problems/count-beautiful-substrings-ii/
from collections import Counter
def solve(s,k):
    base=1
    while base*base%k:base+=1
    period=2*base;balance=answer=0;counts=Counter({(0,0):1})
    for i,c in enumerate(s,1):
        balance+=1 if c in 'aeiou' else -1;key=(i%period,balance);answer+=counts[key];counts[key]+=1
    return answer
