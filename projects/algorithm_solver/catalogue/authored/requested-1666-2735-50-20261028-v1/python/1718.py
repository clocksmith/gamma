"""Original candidate; no qualification or admission."""

def solve(n):
    out=[0]*(2*n-1)
    def place(index,used):
        while index<len(out) and out[index]:index+=1
        if index==len(out):return True
        for value in range(n,0,-1):
            if used>>value&1:continue
            other=index if value==1 else index+value
            if other>=len(out) or out[other]:continue
            out[index]=out[other]=value
            if place(index+1,used|(1<<value)):return True
            out[index]=out[other]=0
        return False
    place(0,0);return out


class Solution:
    def constructDistancedSequence(self, n):
        return solve(n)
