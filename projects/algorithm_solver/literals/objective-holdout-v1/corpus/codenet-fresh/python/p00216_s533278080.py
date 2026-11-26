pre = 4280
v = [0,125,140,160]
while True:
    w = int(input())
    if w == -1:break

    s= 1150

    
    amari = w

    for i in reversed(range(1,4)):
        if amari > i*10:
            spam = amari - i*10
            s += spam * v[i]
            amari = i*10

    print (pre - s)