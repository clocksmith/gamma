import sys
ab = []
for line in sys.stdin:
    temp = list(map(int, line.split()))
    if temp == [0, 0]:
        v = [0 for i in range(max(ab)+1)]
        for i in ab:
            v[i] += 1
        odd = 0
        for i in v:
            if i % 2 == 1:
                odd += 1
        if odd == 2 and ((v[1] % 2) == (v[2] % 2) == 1):
            print('OK')
        else:
            print('NG')
        ab = []
    else:
        ab += temp

