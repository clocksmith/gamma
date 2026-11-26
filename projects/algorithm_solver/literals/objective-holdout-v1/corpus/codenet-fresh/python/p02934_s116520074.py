n = int(input())
a = [int(i) for i in input().split()]
b = 1/a[0]
for i in range(1,n):
    b += 1/a[i]
print(1/b)