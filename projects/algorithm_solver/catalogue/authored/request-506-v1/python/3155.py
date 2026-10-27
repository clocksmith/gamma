# Original candidate. Contract: https://leetcode.com/problems/maximum-number-of-upgradable-servers/
def solve(count, upgrade, sell, money):
    return [min(c,(m+c*s)//(u+s)) for c,u,s,m in zip(count,upgrade,sell,money)]
