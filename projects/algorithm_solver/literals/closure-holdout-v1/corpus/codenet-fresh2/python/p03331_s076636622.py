n = int(input())
res = n
for i in range(1,n//2+1):
    tmp = 0
    a = str(n-i)
    b = str(i)
    for j in a:
        tmp += int(j)
    for j in b:
        tmp += int(j)
    res = min(res,tmp)
else:
    print(res)