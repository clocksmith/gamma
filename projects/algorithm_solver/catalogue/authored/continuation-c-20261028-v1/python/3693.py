def solve(n, costs):
    recent = [0, float('inf'), float('inf')]
    for i in range(1,n+1):
        value = costs[i-1]+min(recent[(i-j)%3]+j*j for j in range(1,min(3,i)+1))
        recent[i%3] = value
    return recent[n%3]

class Solution:
    def climbStairs(self, n, costs):
        return solve(n, costs)
