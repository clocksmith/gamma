K = int(input())
count = 1
n = 0
if K % 2 == 0 or K % 5 == 0:
    count = -1
    print(count)
else:
    while True:
        n = (n*10+7)%K
        if n == 0:
            break
        count += 1
    print(count)