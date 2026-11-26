a, b, c, d = map(int, input().split())

if (a<=c and b<=c) or (c<=a and d<=a):
    print(0)
else:
    print(min(b,d)-max(a,c))
