import sys

sys.setrecursionlimit(10 ** 6)
int1 = lambda x: int(x) - 1
p2D = lambda x: print(*x, sep="\n")

def main():
    m,n = list(map(int, input().split()))
    md=10**9+7
    print(pow(m,n,md))
main()

