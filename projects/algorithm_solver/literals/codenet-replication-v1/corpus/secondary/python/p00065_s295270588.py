#import math

listc = [0]*1001
cnt = [0]*1001
n = 0

while True:
    try:
        c, d = list(map(int, input().split(',')))
    except:
        break
    listc[c] = 1
    cnt[c] += 1

while True:
    try:
        c, d = list(map(int, input().split(',')))
    except:
        break
    if listc[c] == 1:
        listc[c] = 2
    cnt[c] += 1

for c in range(1,1001):
    if listc[c] == 2:
        print(c,cnt[c])

