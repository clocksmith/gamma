# Original candidate implementation. Contract: https://leetcode.com/problems/find-the-first-player-to-win-k-games-in-a-row/
def solve(skills,k):
    champion=0;wins=0
    for i in range(1,len(skills)):
        if skills[i]>skills[champion]: champion=i; wins=0
        wins+=1
        if wins>=k: return champion
    return champion
