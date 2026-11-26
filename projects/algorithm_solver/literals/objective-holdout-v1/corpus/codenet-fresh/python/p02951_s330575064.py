a, b, c = map(int, input().split())

if a < b + c:
    print(c - (a - b))
else:
    print(0)