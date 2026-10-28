"""Separate O(n) positive-window variant; caller array is immutable."""
def solve(arr: list[int], target: int) -> int:
    n=len(arr)
    shortest=[n+1]*(n+1)
    answer=n+1
    left=total=0
    for right,value in enumerate(arr):
        total+=value
        while total>target:
            total-=arr[left]
            left+=1
        shortest[right+1]=shortest[right]
        if total==target:
            length=right-left+1
            answer=min(answer,length+shortest[left])
            shortest[right+1]=min(shortest[right+1],length)
    return -1 if answer==n+1 else answer
class Solution:
    def minSumOfLengths(self,arr: list[int],target: int) -> int:
        return solve(arr,target)
