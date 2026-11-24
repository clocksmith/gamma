z='abcdefghijklmnopqrstuvwxyz'
e=lambda x,i,j:z[(z.index(x)*i+j)%26]
def f():
 for i in range(1,26,2):
  for j in range(26):
   if''.join(e(c,i,j)for c in'that')in s or''.join(e(c,i,j)for c in'this')in s:return(i,j)
def g(x,y,s=0,t=1):
 q,r=x//y,x%y
 return g(y,r,t,s-q*t) if r else t
for _ in[0]*int(input()):
 s=input()
 a,b=f()
 h=g(26,a)
 print(''.join(z[h*(z.index(c)-b)%26]if c in z else c for c in s))
