a, b = map(int, input().split(' '))
kuchi = 1
count = 0
while kuchi < b:
    kuchi += a - 1
    count += 1
print(count)