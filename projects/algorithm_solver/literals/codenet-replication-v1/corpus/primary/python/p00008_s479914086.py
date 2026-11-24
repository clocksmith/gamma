while True:
    try:
        n = int(input())
    except:
        break
    x = 0
    for a in range(0, 10):
        for b in range(0, 10):
            for c in range(0, 10):
                for d in range(0, 10):
                    x += (a + b + c + d == n)
    print(x)

