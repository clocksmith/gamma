def s():
 import sys
 r=sys.stdin.readline
 for e in iter(r,'0 0\n'):
  N,M=map(int,e.split())
  k,p=1,0
  S=[int(r()) for _ in[0]*N]
  for d in[int(r())for _ in[0]*M]:
   p+=d if N<=p+d else d+S[p+d]
   if N<=p+1:break
   k+=1
  print(k)
if'__main__'==__name__:s()
