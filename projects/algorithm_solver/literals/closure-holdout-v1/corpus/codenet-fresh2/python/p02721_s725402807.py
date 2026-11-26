
def resolve():
    def sub(s):
        cur = 0
        last = -(C + 1)
        res = [0] * (N + 1)
        for i in range(N):
            if i - last > C and s[i] == "o":
                cur += 1
                last = i
            res[i + 1] = cur
        return res

    N, K, C = map(int, input().split())
    S = input()

    left = sub(S)
    T = S[::-1]
    right = sub(T)
    for i in range(N):
        if S[i] == "x":
            continue
        if left[i] + right[N - i - 1] < K:
            print(i + 1)


if __name__ == "__main__":
    resolve()
