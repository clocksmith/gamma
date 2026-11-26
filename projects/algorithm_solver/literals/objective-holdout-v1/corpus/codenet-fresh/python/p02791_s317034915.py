n = int(input())
p = [int(i) for i in input().split()]
count = 0
point_min = p[0]
for i in p:
    if i <= point_min:
        count += 1
        point_min = i
print(count)