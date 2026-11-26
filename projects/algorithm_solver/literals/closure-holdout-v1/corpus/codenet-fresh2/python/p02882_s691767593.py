from math import atan2, pi
a,b,x = map(int, input().split())

S = a * a * b

if x / S >= 0.5:
    n = 2*(x - S) / (a * a)
    print(abs(atan2(n, a) * 180 / pi))
else:
    n = 2 * x / (a * b)
    print(abs(atan2(b, n) * 180 / pi))
