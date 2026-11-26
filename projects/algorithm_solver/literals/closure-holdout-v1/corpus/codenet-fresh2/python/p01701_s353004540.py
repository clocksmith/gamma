from fractions import Fraction

while True:
    s = input()
    if s == '#':
        break
    N = len(s)
    if s[-1] == 't':
        ans = Fraction(90)
        p = 4
    else:
        ans = Fraction(0)
        p = 5
    i = 1
    while p < N:
        if s[-1-p] == 't':
            ans += Fraction(90, 1 << i)
            p += 4
        else:
            ans -= Fraction(90, 1 << i)
            p += 5
        i += 1
    print(ans)