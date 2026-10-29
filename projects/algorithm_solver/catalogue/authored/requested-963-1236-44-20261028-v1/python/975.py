"""Original candidate; no qualification or admission."""

def solve(arr):
    n=len(arr)
    def next_indices(order):
        nxt=[-1]*n;stack=[]
        for i in order:
            while stack and stack[-1]<i:nxt[stack.pop()]=i
            stack.append(i)
        return nxt
    higher=next_indices(sorted(range(n),key=lambda i:(arr[i],i)))
    lower=next_indices(sorted(range(n),key=lambda i:(-arr[i],i)))
    odd=[False]*n;even=[False]*n;odd[-1]=even[-1]=True
    for i in range(n-2,-1,-1):
        if higher[i]>=0:odd[i]=even[higher[i]]
        if lower[i]>=0:even[i]=odd[lower[i]]
    return sum(odd)


class Solution:
    def oddEvenJumps(self, arr):
        return solve(arr)
