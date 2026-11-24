import sys
import math
datasets = []
ans = []
while 1:
    n = int(input())
    if n == 0:
        break
    datasets.append(n)
for n in datasets:
    facts = []
    for x in range(1, int((math.sqrt(2*n)))+1 ):
        if 2*n%x == 0:
            facts.append(x)
    for x in reversed(facts):
        y = 2*n // x
        if (y-x)%2 == 1:
            ans.append((x, y))
            break
for i in range(len(datasets)):
    x = ans[i][0]
    y = ans[i][1]
    print("{} {}".format((y-x+1)//2, x))
    
