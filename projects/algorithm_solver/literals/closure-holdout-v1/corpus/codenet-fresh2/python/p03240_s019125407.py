n = int(input())
data = [list(map(int, input().split())) for _ in range(n)]
for c_x in range(101):
    for c_y in range(101):
        valid = True
        H = None
        # h==0でも情報はあって、これを逃さない
        for i in range(n):
            x, y, h = data[i]
            if h >= 1:
                H = h + abs(x-c_x) + abs(y-c_y)
                break
        for i in range(n):
            x, y, h = data[i]
            if h != max(H - abs(x-c_x) - abs(y-c_y), 0):
                valid = False
                break
        if valid:
            print(c_x, c_y, H)
