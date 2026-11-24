def g(a, b):
    while b:
        a, b = b, a%b
    return a
n = int(input())
a = list(map(int, input().split()))
ans = a[0]*a[1]/g(a[0],a[1])
for i in a[2:]:
    ans = ans*i/g(ans,i)
print(int(ans))
