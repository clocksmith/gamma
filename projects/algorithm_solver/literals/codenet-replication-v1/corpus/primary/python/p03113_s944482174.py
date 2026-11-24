I=lambda:map(int,input().split())
n,k=I()
l=[[a-1,i]for i,a in enumerate(I(),1)]
for a,_ in l:
  if a<0:
    print(-1)
    exit()
l.sort(reverse=1)
r=[i for _,i in l]
b=r[-1]
for i in range(k):
  for t in l:
    if t[1]==b:continue
    if not t[0]:
      print(-1)
      exit()
    t[0]-=1
    r.append(t[1])
  l.sort(reverse=1)
  b=r[-1]
print(len(r))
print(*r)