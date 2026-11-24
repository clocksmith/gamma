n=int(input())
for i in range(1,1000):
  if i*(i+1)//2==n:
    D=[[0]*i for l in range(i)]
    stopcnt=i
    cnt=0
    a,b=0,0
    print('Yes')
    print(i+1)
    for j in range(n):
      D[a][j-b]=j+1
      cnt+=1
      if cnt==stopcnt:
        a+=1
        b+=stopcnt-1
        cnt=0
        stopcnt-=1
    for a in range(i):
      for b in range(a,i):
        D[b][a]=D[a][b]
    DD=[]
    for j in range(i):
      DD.append(D[j][j])
    D.append(DD)
    for j in D:
      print(len(j),*j)
    exit()
print('No')
