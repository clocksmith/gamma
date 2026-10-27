# Original candidate. Contract: https://leetcode.com/problems/minimum-levels-to-gain-more-points/
def solve(possible):
    total=sum(2*x-1 for x in possible);prefix=0
    for i in range(len(possible)-1):
        prefix+=2*possible[i]-1
        if 2*prefix>total:return i+1
    return -1
