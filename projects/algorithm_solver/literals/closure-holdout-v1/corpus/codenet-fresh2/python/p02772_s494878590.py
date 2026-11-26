N=int(input())
A=list(map(int,input().split()))
ans="APPROVED"

for i in range(N):
    if A[i]%2==0:
        if A[i]%3==0 or A[i]%5==0:
            pass
        else:
            ans="DENIED"
    else:
        pass

print(ans)