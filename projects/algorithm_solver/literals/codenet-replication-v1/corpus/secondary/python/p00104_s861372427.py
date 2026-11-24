import sys
readline = sys.stdin.readline
write = sys.stdout.write

dd = ((-1, 0), (0, -1), (1, 0), (0, 1))
df = "<^>v".find

def solve():
    H, W = map(int, readline().split())
    if H == 0:
        return False
    MP = [readline().strip() for i in range(H)]
    x = y = 0
    used = [[0]*W for i in range(H)]
    used[0][0] = 1
    while 1:
        i = df(MP[y][x])
        if i == -1:
            write("%d %d\n" % (x, y))
            return True
        dx, dy = dd[i]
        x += dx; y += dy
        if used[y][x]:
            write("LOOP\n")
            return True
        used[y][x] = 1
while solve():
    ...
