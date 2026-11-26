n,x = map(int,input().split())
l = [int(i) for i in input().split()]
d = [0]
count = 1
for i in range(1,n+1):
    d.append(d[i-1]+l[i-1])
    if d[i] <= x:
        count += 1
print(count)