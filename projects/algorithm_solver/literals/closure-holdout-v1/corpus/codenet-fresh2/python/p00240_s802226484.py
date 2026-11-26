while 1:
    N = int(input())
    if N == 0:
        break
    y = int(input())
    v = 0; k = None
    for i in range(N):
        b, r, t = map(int, input().split())
        if t == 1:
            w = 1 + y * r /100
        else:
            w = (1 + r / 100) ** y
        if v < w:
            v = w
            k = b
    print(k)
