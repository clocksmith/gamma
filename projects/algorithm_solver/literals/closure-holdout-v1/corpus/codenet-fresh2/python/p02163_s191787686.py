n = int(input())
a, b = 1, 0
for i in range(n) :
    q, x = map(int, input().split())
    if q == 1 :
        a *= x
        b *= x
    elif q == 2 :
        b += x
    elif q == 3 :
        b -= x
print(-b, a)
