def main():
    N = int(input())
    ans = N*(N**2 + 3*N + 2)//6
    for _ in range(N-1):
        a, b = (int(i) for i in input().split())
        if a > b:
            a, b = b, a
        ans -= a*(N-b+1)
    print(ans)


if __name__ == '__main__':
    main()
