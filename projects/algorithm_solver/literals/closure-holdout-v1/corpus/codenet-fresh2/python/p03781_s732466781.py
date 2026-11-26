x = int(input())
d = 0
for i in range(1, 10 ** 6):
    d += i
    if x <= d:
        print(i)
        break
