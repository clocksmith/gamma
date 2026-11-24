n = int(input())
S = input()

def rev(anim):
    if anim == 'S':
        return 'W'
    else:
        return 'S'

def check(comb, ans):
    if comb[1] == 'S':
        if ans == 'o':
            return comb[0] == comb[2]
        else:
            return comb[0] != comb[2]
    else:
        if ans == 'o':
            return comb[0] != comb[2]
        else:
            return comb[0] == comb[2]

import sys
for T in ('SS', 'SW', 'WS', 'WW'):
    for i in range(2, n):
        ans = S[i-1]
        anim = T[i-1]
        prev = T[i-2]
        if ans == 'o':
            if anim == 'S':
                T += prev
            else:
                T += rev(prev)
        else:
            if anim == 'S':
                T += rev(prev)
            else:
                T += prev
    comb1 = T[n-2]+T[n-1]+T[0]
    ans1 = S[n-1]
    comb2 = T[n-1]+T[0]+T[1]
    ans2 = S[0]
    if check(comb1, ans1) and check(comb2, ans2):
        print(T)
        sys.exit(0)
print(-1)
