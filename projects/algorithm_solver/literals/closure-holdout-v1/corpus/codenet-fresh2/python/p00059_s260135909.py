while 1:
    try:
        xa1, ya1, xa2, ya2, xb1, yb1, xb2, yb2 = map(float, input().split())
        if max(xa1, xb1) <= min(xa2, xb2) and max(ya1, yb1) <= min(ya2, yb2):
            print('YES')
        else:
            print('NO')

    except:
        break

