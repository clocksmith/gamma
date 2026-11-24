
N = int(input())

txy = [list(map(int, input().split())) for _ in range(N)]

point = [0,0]
flag = "Yes"
t = 0
for i in txy:
    t_, x, y = i
    t__ = t_ - t 
    move = abs(x-point[0])+abs(y-point[1])
    if move > t__:
        flag = "No"
        break
    elif (t__ - move) % 2 == 1:
        flag = "No"
        break
    point = [x,y]
    t = t_

print(flag)