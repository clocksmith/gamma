# -*- coding: utf_8 -*-

def check(t, n, k, p):
    i = 0
    for j in range(k):
        s = 0
        while (s + t[i] <= p):
            s += t[i]
            i += 1
            if i == n:
                return n
    return i

if __name__ == "__main__":
    n, k = [int (x) for x in input().split()]
    t = []
    for i in range(n):
        t.append(int(input()))

    start, end = 0, 10000 * 100000

    while (end - start > 1):
        mid = (start + end) // 2
        v = check(t, n, k, mid)
        if v >= n:
            end = mid
        else:
            start = mid

    print(end)