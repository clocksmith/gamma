# Original candidate. Contract: https://leetcode.com/problems/maximum-points-after-enemy-battles/
def solve(enemyEnergies, currentEnergy):
    smallest=min(enemyEnergies)
    if currentEnergy<smallest:return 0
    return (currentEnergy+sum(enemyEnergies)-smallest)//smallest
