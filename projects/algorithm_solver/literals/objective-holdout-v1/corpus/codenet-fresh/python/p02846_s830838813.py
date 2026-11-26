T1,T2 = map(int,input().split())
A1,A2 = map(int,input().split())
B1,B2 = map(int,input().split())
T = T1 + T2
C = A1*T1+A2*T2
D = B1*T1+B2*T2
if C == D:
    print("infinity")
    exit()
if C > D:
    A1,B1=B1,A1
    A2,B2=B2,A2
    C,D  = D,C
if A1 < B1:
    print(0)
    exit()
ok = 0
ng = pow(10,30)
while ng - ok > 1:
    md = (ok + ng)//2
    if A1*T1+C*md>=B1*T1+D*md:
        ok = md
    else:
        ng = md
ans = 2*ok + 1
if A1*T1+C*ok == B1*T1+D*ok:
    ans -= 1
print(ans)
