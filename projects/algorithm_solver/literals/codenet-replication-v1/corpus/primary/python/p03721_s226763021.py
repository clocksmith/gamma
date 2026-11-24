n , k = map(int, input().split())
data = []
for i in range(n):
    data.append(list(map(int, input().split())))
data.sort()
total = 0
for i in data:
    if total < k <= total + i[1]:
        print(i[0])
        exit()
    else:
        total += i[1]