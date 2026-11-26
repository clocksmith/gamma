def main():
    n = int(input())
    a = list(map(int, input().split()))
    d = [[(j, i), (-1, -1)] for i, j in enumerate(a)]
    ans = 0
    for i in range(1, 2**n):
        (t1, t2), (t3, t4) = d[i]
        for j in range(n):
            (t5, t6), (t7, t8) = d[i & ~(1 << j)]
            if t6 not in [t2, t4]:
                if t5 > t1:
                    t1, t2, t3, t4 = t5, t6, t1, t2
                elif t5 > t3:
                    t3, t4 = t5, t6
            if t8 not in [t2, t4]:
                if t7 > t3:
                    t3, t4 = t7, t8
        d[i] = [(t1, t2), (t3, t4)]
        ans = max(ans, t1+t3)
        print(ans)


main()