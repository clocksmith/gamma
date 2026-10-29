"""Original candidate; no qualification or admission."""

def solve(arr):
    values=list(arr);out=[]
    for end in range(len(values),1,-1):
        at=max(range(end),key=values.__getitem__)
        if at==end-1:continue
        if at:values[:at+1]=reversed(values[:at+1]);out.append(at+1)
        values[:end]=reversed(values[:end]);out.append(end)
    return out


class Solution:
    def pancakeSort(self, arr):
        return solve(arr)
