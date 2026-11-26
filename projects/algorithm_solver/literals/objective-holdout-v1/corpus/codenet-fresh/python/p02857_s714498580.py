N = int(input())

def ask1(n):
  s = ['?'] + [i for i in range(n,n+N)]
  print(*s)
  return input()

def ask2(a,l,r):
  if l == r:
    s = ['?'] + [a] 
  else:
    s = ['?'] + [a] + [i for i in range(l,r+1)]
  print(*s)
  return input()

def ask3(a,l,r):
  if l == r:
    s = ['?'] + [a] 
  elif l < 1:
    s = ['?'] + [a] + [i for i in range(N+2,N*2+1)]
  elif r > N*2:
    s = ['?'] + [a] + [i for i in range(1,N)]
  else:
    s = ['?'] + [a] + [i for i in range(1,l+1)] + [i for i in range(r,N*2+1)]
  print(*s)
  return input()

#print(ask1(10))
#print(ask2(1,4,7))
#print(ask3(7,4,11))
#exit()

ans = ['' for _ in range(N*2)]

a = ask1(1)
if a == 'Red':
  LC = 'Red'
else:
  LC = 'Blue'

l = 1
r = N+1
while(l+1 < r):
  m = (l+r)//2
  a = ask1(m)
  if a == LC:
    l = m
  else:
    r = m

sl = r
sr = l+N-1
for i in range(1,N*2+1):
  if sl <= i <= sr:
    a = ask3(i,sl-2,sr+2)
  else:
    a = ask2(i,sl,sr)
  if a == 'Red':
    ans[i-1] = 'R'
  else:
    ans[i-1] = 'B'
  
print('! '+''.join(ans))