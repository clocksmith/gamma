import sys

sys.setrecursionlimit(10 ** 6)
input = sys.stdin.readline
int1 = lambda x: int(x) - 1
p2D = lambda x: print(*x, sep="\n")

def main():
    n, k = map(int, input().split())
    if 2 * k - n > 1:
        print(-1)
        exit()
    a = k + n // 2
    b = k + n
    c = k + 2 * n
    ab = []
    for i in range(n):
        ab.append([a, b])
        a, b = a + 1, b + 1
        if a == k + n: a = k
    ab.sort(key=lambda x: x[0] + x[1])
    for a, b in ab:
        print(a, b, c)
        c += 1

main()
