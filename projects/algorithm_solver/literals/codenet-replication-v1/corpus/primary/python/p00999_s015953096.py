while 1:
    a, b, c, d, e = map(int, input().split())
    if a == b == c == d == e == 0:
        break
    na, nb, nc = map(int, input().split())
    if nc >= d:
        print(e * nc + b * nb + a * na)
        continue
    lst = [c] * nc + [b] * nb + [a] * na
    if na + nb + nc > d:
        print(min(sum(lst[:d]), e*d) + sum(lst[d:]))
    else:
        print(min(sum(lst), e*d))
