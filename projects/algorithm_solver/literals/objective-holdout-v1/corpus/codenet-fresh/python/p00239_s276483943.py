while 1:
    n = int(input())
    if n == 0:break
    s = []
    for _ in range(n):s.append(tuple(map(int, input().split())))
    l = tuple(map(int, input().split()))
    e = []
    for i in range(n):
        if s[i][1] <= l[0] and s[i][2] <= l[1] and s[i][3] <= l[2] and s[i][1] * 4 + s[i][2] * 9 + s[i][3] * 4 <= l[3]:e.append(s[i][0])
    if e != []:
        for i in e:print(i)
    else:print("NA")
