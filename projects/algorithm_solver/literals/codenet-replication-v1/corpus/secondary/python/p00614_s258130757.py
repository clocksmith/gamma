while True:
    p, n1, n5, n10, n50, n100, n500 = map(int, input().split())
    if p == 0:break
    values = (500, 100, 50, 10, 5, 1)
    values_cnt = (n500, n100, n50, n10, n5, n1)
    INF = 10 ** 20


    def return_cnt(x):
        ret = 0
        for value in values:
            ret += x // value
            x %= value
        return ret


    def make_price(x):
        ret = 0
        for value, cnt in zip(values, values_cnt):
            available_cnt = x // value
            ret += min(available_cnt, cnt)
            x -= value * min(available_cnt, cnt)
        if x == 0:return ret
        return INF


    print(min([make_price(i) + return_cnt(i - p) for i in range(p, p + 500)]))


