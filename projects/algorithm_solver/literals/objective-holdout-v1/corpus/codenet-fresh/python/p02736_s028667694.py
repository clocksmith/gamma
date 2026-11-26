N = int(input())
a = list(map(int,list(input())))
a = list(map(lambda x:x-1,a))
x = 0
num_mod = [0]*N
for i in range(1,N):
  tmp = 0
  t = i
  while t%2==0:
    t//=2
    tmp+=1
  num_mod[i] = num_mod[i-1]+tmp
  
for i,n in enumerate(a):
  if n%2==0:
    continue
  else:
    if num_mod[N-1]==(num_mod[i]+num_mod[N-1-i]):
      x+=1

if x%2!=0:
  print(1)
  
elif 1 in a:
  print(0)

else:
  a = [x//2 for x in a]
  x = 0
  for i,n in enumerate(a):
    if n%2==0:
      continue
    else:
      if num_mod[N-1]==(num_mod[i]+num_mod[N-1-i]):
        x+=1
  if x%2!=0:
    print(2)
  else:
    print(0)