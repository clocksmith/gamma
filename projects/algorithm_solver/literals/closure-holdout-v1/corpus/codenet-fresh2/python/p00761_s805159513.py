while True:
    a0, l = map(int, input().split())
    if a0 == 0 and l == 0: break
    seq = [a0]
    a = str(a0)
    for i in range(20):
        if len(a) < l:
            a = '0' * (l - len(a)) + a
        a_min = int(''.join(sorted(list(a))))
        a_max = int(''.join(sorted(list(a), reverse=True)))
        ai = a_max - a_min
        if ai in seq:
            j = seq.index(ai)
            print(j, ai, (i+1)-j)
            break
        else:
            seq.append(ai)
            a = str(ai)