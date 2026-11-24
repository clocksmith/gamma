from collections import Counter
from itertools import product

n = int(input())
d = Counter(list(map(int, input().split())) + [0])

ans, cnt = [], []
for num in d:
    if d[num] > (2 - (num in {0, 12})):
        print(0)
        exit()
    elif (num in {0, 12}) and d[num] == 1:
        ans.append(num)
    elif d[num] == 2:
        ans.append(num), ans.append(24 - num)
    elif d[num] == 1:
        cnt.append(num)

s = 0
if len(cnt) == 0:
    s = min(ans[i] - ans[i - 1] for i in range(1, len(ans)))
for bit in product([1, -1], repeat=len(cnt)):
    tmp = ans[:]
    tmp += [(ci - 12) * bi + 12 for bi, ci in zip(bit, cnt)]
    tmp = sorted(tmp + [i + 24 for i in tmp])
    stmp = min(tmp[i] - tmp[i - 1] for i in range(1, len(tmp)))
    s = max(s, stmp)
print(s)
