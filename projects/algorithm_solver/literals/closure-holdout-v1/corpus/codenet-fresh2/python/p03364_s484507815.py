N=int(input())
S=["" for i in range(N)]

for i in range(N):
    S[i]=input()

count=0

for l in range(N):
    JUDGE=1
    for j in range(N):
        for k in range(j+1,N):
            
            if S[j][k-l]!=S[k][j-l]:
                JUDGE=0
                break
        if JUDGE==0:
            break

    if JUDGE==1:
        count+=1

print(count*N)
