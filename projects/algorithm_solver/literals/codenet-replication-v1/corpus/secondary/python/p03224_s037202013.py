from math import sqrt, floor
from itertools import combinations
from collections import defaultdict
N = int(input())

ans_root = sqrt(1 + 8 * N)
if (1 + 8 * N) - floor(ans_root) ** 2 > 1e-6:
    print("No")
    exit(0)

k = floor((1 + ans_root) // 2)
result = defaultdict(list)
for i, (flag1, flag2) in enumerate(combinations(range(k), 2), start=1):
    result[flag1].append(str(i))
    result[flag2].append(str(i))

print("Yes")
print(k)
for value in result.values():
    print(len(value), " ".join(value))
