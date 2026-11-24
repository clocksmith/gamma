from itertools import chain, repeat

def solve(a, x, y):
    a[y][x] = 0
    for dx, dy in chain(zip(range(-3, 4), repeat(0)), zip(repeat(0), range(-3, 4))):
        if a[y+dy][x+dx]:
            solve(a, x+dx, y+dy)

for i in range(1, int(input())+1):
    input()
    empty = [[0]*14]*3
    a = empty + [[0,0,0]+list(map(int, input()))+[0,0,0] for _ in [0]*8] + empty
    x, y = int(input()), int(input())
    solve(a, x+2, y+2)

    print("Data {}:".format(i))
    for l in a[3:-3]:
        print("".join(map(str, l[3:-3])))

