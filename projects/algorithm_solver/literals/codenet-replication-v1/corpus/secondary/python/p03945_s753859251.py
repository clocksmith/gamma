s=input()
n=len(s)
tmp=s[0]
cnt=0
for i in range(1, n):
    if s[i]!=tmp:
        tmp=s[i]
        cnt+=1
print(cnt)