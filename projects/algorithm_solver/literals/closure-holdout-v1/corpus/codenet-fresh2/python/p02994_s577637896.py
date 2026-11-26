n, l = (int(i) for i in input().split())

min_diff = 10000
min_num = 0
aa = 0
for x in range(l,l+n):
    aa += x
    if min_diff > abs(x):
        min_diff = abs(x)
        min_num = x

print(aa - min_num)
