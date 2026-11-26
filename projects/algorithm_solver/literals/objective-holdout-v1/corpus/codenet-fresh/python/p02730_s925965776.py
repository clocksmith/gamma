S=input()
N=len(S)
f=True
for i in range(N//2):
    if S[i]!=S[-1-i]:f=False
if f==True:
    s1=S[0:(N-1)//2]
    s2=S[(N+3)//2-1::]
    for i in range(N//2//2):
        if s1[i]!=s1[-1-i] or s2[i]!=s2[-1-i]:f=False
print("Yes") if f==True  else print("No")
