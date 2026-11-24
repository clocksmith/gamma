n = int(input())
x, y = 20, 0
for _ in range(n):
    a, b = map(int, input().split())
    if y < b:
        x, y = a, b
    elif y == b and x >= a:
        x, y = a, b
print(x, y)
