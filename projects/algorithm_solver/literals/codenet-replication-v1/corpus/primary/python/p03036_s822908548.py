r, d, x = map(int, input().split())
for i in range(2001, 2011):
    x = r*x - d
    print(x)

