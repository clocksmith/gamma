def main():
    N, K = map(int, input().split())
    A = [0] + list(map(int, input().split()))

    for i in range(N):
        A[i + 1] += A[i]

    B = [A[j] - A[i] for i in range(N) for j in range(i + 1, N + 1)]

    ans = 0
    t = 40
    while t:
        count = 0
        tmp = pow(2, t -1)
        for b in B:
            if ((b & (tmp + ans)) == (tmp + ans)):
                count += 1
            if count >= K:
                ans += tmp
                break
        t -= 1

    print (ans)

if __name__ == '__main__':
    main()