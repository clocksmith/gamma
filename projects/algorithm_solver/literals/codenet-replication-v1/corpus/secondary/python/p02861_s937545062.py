import itertools

n = int(input())
towns = [tuple(map(int, input().split())) for _ in range(n)]

def calc(i, j):
    return ((towns[i][0] - towns[j][0])**2 + (towns[i][1] - towns[j][1])**2)**0.5

l = list(range(n))
p = list(itertools.permutations(l, n))

total = 0
for p_ in p:
    for i in range(n-1):
        total += calc(p_[i], p_[i+1])

res = total / len(p)

print(res)