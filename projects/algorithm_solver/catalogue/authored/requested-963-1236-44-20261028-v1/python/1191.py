"""Original candidate; no qualification or admission."""

def solve(arr,k):
    total=sum(arr);best=current=0
    for i in range(len(arr)*min(k,2)):
        current=max(0,current+arr[i%len(arr)]);best=max(best,current)
    return (best+max(0,total)*(k-2 if k>2 else 0))%1000000007


class Solution:
    def kConcatenationMaxSum(self, arr, k):
        return solve(arr, k)
