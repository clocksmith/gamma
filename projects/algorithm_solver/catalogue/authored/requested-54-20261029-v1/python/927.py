"""Original development candidate; independent qualification pending."""
def solve(arr):
    ones = [i for i,x in enumerate(arr) if x]
    if not ones:
        return [0,2]
    if len(ones)%3:
        return [-1,-1]
    group = len(ones)//3
    a,b,c = ones[0],ones[group],ones[2*group]
    size = len(arr)-c
    if a+size > b or b+size > c:
        return [-1,-1]
    if arr[a:a+size] == arr[b:b+size] == arr[c:]:
        return [a+size-1,b+size]
    return [-1,-1]


class Solution:
    def threeEqualParts(self, arr):
        return solve(arr)
