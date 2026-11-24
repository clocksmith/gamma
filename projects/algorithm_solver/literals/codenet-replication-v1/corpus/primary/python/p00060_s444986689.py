while True:
    try:
        x,y,z = map(int,input().split())
    except EOFError:
        break
    cnt = 0
    for i in range(1,10):
        if i == x or i == y or i == z:
            continue
        if x + y + i <= 20:
            cnt += 1
    if cnt >= 4:
        print('YES')
    else:
        print('NO')