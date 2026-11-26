h,w=map(int,input().split())
n=int(input())
l=list(map(int,input().split()))
count=0
ans=[["0" for i in range(w)] for j in range(h)]
now=0
index=0
locate=[0,0]
while count<h*w:
  count+=1
  if now==0:
    now+=l[index]
    index+=1
  x=locate[0]
  y=locate[1]
  ans[x][y]=str(index)
  if x%2==0:
    if y<w-1:
      y+=1
    else:
      x+=1
  else:
    if y!=0:
      y-=1
    else:
      x+=1
  now-=1
  locate=[x,y]
for i in range(h):
  print(" ".join(ans[i]))