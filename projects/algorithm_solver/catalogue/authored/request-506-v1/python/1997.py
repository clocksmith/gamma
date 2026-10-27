# Original implementation. Contract: https://leetcode.com/problems/first-day-where-you-have-been-in-all-the-rooms/
def solve(nextVisit):
    d=[0]*len(nextVisit)
    for i in range(1,len(d)): d[i]=(2*d[i-1]-d[nextVisit[i-1]]+2)%1000000007
    return d[-1]
