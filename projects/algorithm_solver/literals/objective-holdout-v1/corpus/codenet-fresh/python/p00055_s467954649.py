while True:
    try:
        f = float(input())
    except:
        break
    l = [0] * 11
    l[1] = f
    for i in range(2,11):
        if i % 2 == 0:
            l[i] = l[i-1] * 2
        else:
            l[i] = l[i-1] / 3

    print(sum(l))