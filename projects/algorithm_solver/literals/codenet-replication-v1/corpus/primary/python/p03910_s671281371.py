n=int(input())
ans=int(0)
check=int(0)
A=[]
for i in range(1,n*100):
    ans+=i
    A.append(i)
    if ans>=n:
        break

check=ans-n
for i in range(len(A)):
    if i==check-1:
        continue
    else:
        print(A[i])