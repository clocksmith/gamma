N = int(input())
a = [int(input()) for _ in range(N)]
count = 0
light = 1

while True:
    light = a[light - 1]
    count += 1

    if light == 2:
        print(count)
        break
    if count == N - 1:
        print(-1)
        break