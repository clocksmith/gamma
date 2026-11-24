import math
while True:
    try:
        x1, y1, x2, y2, x3, y3, xp, yp = map(float, input().split())
    except:
        break
    x = [x1, x2, x3, x1]
    y = [y1, y2, y3, y1]
    x = list(map(lambda i: i - xp, x))
    y = list(map(lambda i: i - yp, y))
    s = lambda a1, a2, b1, b2: abs(a1 * b2 - a2 * b1)
    S3 = sum(s(x[i], y[i], x[i + 1], y[i + 1]) for i in range(3))
    S = s(x[1] - x[0], y[1] - y[0], x[2] - x[0], y[2] - y[0])
    if S3 == S:
        print('YES')
    else:
        print('NO')