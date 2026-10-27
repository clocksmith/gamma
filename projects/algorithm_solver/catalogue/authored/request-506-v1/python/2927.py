# Original candidate implementation. Contract: https://leetcode.com/problems/distribute-candies-among-children-iii/
def solve(n,limit):
    def choose2(v):return v*(v-1)//2 if v>=2 else 0
    return choose2(n+2)-3*choose2(n-limit+1)+3*choose2(n-2*limit)-choose2(n-3*limit-1)
