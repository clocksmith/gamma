n = int(input())
a = list(map(int,input().split()))

for i in a:
    n -= i%2
print(n)

