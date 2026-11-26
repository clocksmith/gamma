N=input()
l=len(N)
ans=0
for i in range(l):
  ans+=int(N[i])
  
if ans%9==0:
  print("Yes")
else:
  print("No")