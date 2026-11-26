while True:

    n = int(input())
    if n == 0:
        break

    ans = 0
    min_bmi = 100000.0
    for l in range(n):
        p,hh,ww = [int(i) for i in input().split()]
        h = float(hh)
        w = float(ww)
        h = h * 0.01

        bmi = abs(w / (h*h) - 22.0)

        if bmi < min_bmi:
            min_bmi = bmi
            ans = p

    print(ans)

