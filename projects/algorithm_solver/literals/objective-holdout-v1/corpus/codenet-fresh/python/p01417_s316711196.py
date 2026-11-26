def main():
    n, m = map(int, input().split())
    import itertools
    full = itertools.combinations(range(n), m)
    l = [list(map(float, input().split())) for i in range(n)]
    # print(l)
    differ = [[0] * n for _ in range(n)]
    for i in range(n):
        for k in range(i + 1, n):
            tmp = 0
            for j in range(3):
                tmp += (l[i][j] - l[k][j]) ** 2
                # print(tmp,l[i][j] , l[k][j])
            differ[i][k] = tmp
            differ[k][i] = tmp
    # print(differ)
    ans = 0
    for f in full:
        tmp = 0
        f = list(f)
        for f1i in range(len(f)):
            for f2i in range(f1i + 1, len(f)):
                tmp += differ[f[f1i]][f[f2i]]
                # print(tmp)
        ans = max(ans, tmp)
    print(ans)



if __name__ == "__main__":
    main()
