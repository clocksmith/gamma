while 1:
    n = int(input())
    if n == 0:
        break

    m = [None] * n
    t = [None] * n
    for i in range(n):
        a = int(input())
        m[i] =  t[i] = a
        for j in range(i):
            t[j] += a
            m[j] = max(m[j], t[j])

    print(max(m))