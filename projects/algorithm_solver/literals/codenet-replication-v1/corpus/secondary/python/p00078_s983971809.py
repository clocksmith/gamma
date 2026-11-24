import sys
for n in map(int, sys.stdin):
    if not n:
        break
    a = [[-1]*(n+2)]+[[-1]+[0]*n+[-1] for _ in [0]*n]+[[-1]*(n+2)]
    x, y = (n+1)//2, (n+1)//2+1
    for i in range(1, n**2+1):
        while a[y][x]:
            if a[y][x] == -1:
                if x in {0, n+1}:
                    x = (1, n)[x==0]
                if y in {0, n+1}:
                    y = (1, n)[y==0]
            else:
                x, y = x-1, y+1
        a[y][x] = i
        x, y = x+1, y+1

    for l in a[1:-1]:
        print("".join(map(lambda x: "{:>4d}".format(x), l[1:-1])))
