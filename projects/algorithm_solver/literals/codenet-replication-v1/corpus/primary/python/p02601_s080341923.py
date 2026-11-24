A,B,C=(input().split())
K = int(input())
A = int(A)
B = int(B)
C = int(C)
for i in range(K):
    if B > C or C == B:
        C = C*2
    elif A > B or B == A:
        B = B*2
if A < B and B < C:
    print("Yes")
else:
    print("No")