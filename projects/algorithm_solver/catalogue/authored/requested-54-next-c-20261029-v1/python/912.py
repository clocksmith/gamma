def solve(nums):
    a = list(nums)
    def sift(root, end):
        while 2*root+1 < end:
            child = 2*root+1
            if child+1 < end and a[child] < a[child+1]:
                child += 1
            if a[root] >= a[child]:
                return
            a[root],a[child] = a[child],a[root]
            root = child
    for i in range(len(a)//2-1,-1,-1):
        sift(i,len(a))
    for end in range(len(a)-1,0,-1):
        a[0],a[end] = a[end],a[0]
        sift(0,end)
    return a

class Solution:
    def sortArray(self, nums):
        return solve(nums)
