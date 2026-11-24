
def solve():
    N = int(input())
    X = [int(i) for i in input().split()]
    M = int(input())
    A = [int(i) for i in input().split()]
    for a in A:
        if not X[a - 1] + 1 in X:
            X[a - 1] = min(X[a - 1] + 1, 2019)
    for x in X:
        print(x)


if __name__ == '__main__':
    solve()

