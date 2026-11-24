import sys
f = sys.stdin


while True:
    n = int(f.readline())
    if n ==0:
        break
    m, star, d = [int(f.readline()) for _ in range(3)]
    lines = [f.readline().strip() for _ in range(d)]
    lots = [None for j in range(d + 1)]
    lots[0] = [i + 1 for i in range(n)]
    for i, line in enumerate(lines):
        lots[i + 1] = lots[i][:]
        for j, c in enumerate(line):
            if c == '1':
                lots[i + 1][j], lots[i + 1][j + 1] = lots[i + 1][j + 1], lots[i + 1][j]
    star = lots[-1][star - 1]
    if m == star:
        print(0)
        continue
    for i, lot in enumerate(lots):
        index_min = min(lot.index(m), lot.index(star))
        index_max = max(lot.index(m), lot.index(star))
        if i and index_max - index_min == 1:
            line = lines[i - 1]
            if (index_min == 0 or line[index_min - 1] == '0') and  line[index_min] == '0' and (index_max == n - 1 or  line[index_max] == '0' ):
                print(i, min(lot.index(m), lot.index(star)) + 1)
                break
        if i == len(lots) - 1:
            print(1)