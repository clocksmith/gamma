"""Original candidate; no qualification or admission."""

from math import perm

def solve(n):
    digits=list(map(int,str(n)));unique=sum(9*perm(9,length-1) for length in range(1,len(digits)));used=set()
    for i,digit in enumerate(digits):
        for value in range(1 if i==0 else 0,digit):
            if value not in used:unique+=perm(9-i,len(digits)-i-1)
        if digit in used:break
        used.add(digit)
    else:unique+=1
    return n-unique


class Solution:
    def numDupDigitsAtMostN(self, n):
        return solve(n)
