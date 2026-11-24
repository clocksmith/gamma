N,K = map(int,input().split())

h = list(map(int,input().split()))

count = 0
for i in h:
    if i >= K:
        count += 1

print(count) 