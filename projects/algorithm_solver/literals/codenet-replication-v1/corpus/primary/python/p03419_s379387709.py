n, m=map(int, input().split())

if n==1 and m==1:
    print(1)
elif n==1 and m!=1:
    print(m-2)
elif n!=1 and m==1:
    print(n-2)
else:
    ans = (m-2)*(n-2)
    print(ans)