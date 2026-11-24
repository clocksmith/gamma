K = int(input())
A,B = map(int,input().split())
flag=0
for i in range(A,B+1):
    if i%K==0:
        flag=1

if flag==1:
    print("OK")
else:
    print("NG")
