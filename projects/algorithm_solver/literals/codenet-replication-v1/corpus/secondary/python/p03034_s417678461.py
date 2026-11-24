def main():
    N = int(input())
    S = list(map(int, input().split()))
    ans = 0
    for C in range(1, N//2+1):
        cs = 0
        for k in range(1, (N-1)//C+1):
            a = C*k
            b = N - a - 1
            if a >= b and (N-1) % C == 0:
                break
            if b <= C:
                break
            cs += S[a] + S[b]
            ans = max(cs, ans)
    print(ans)


if __name__ == "__main__":
    main()
