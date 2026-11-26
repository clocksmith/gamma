def solve(a,b):
  if a+b==0: return [""]
  if a>=5 and b<=4: return [s+"A" for s in solve(a-1,b)]
  if b>=5 and a<=4: return [s+"B" for s in solve(a,b-1)]
  res=[]
  if a>0: res+=[s+"A" for s in solve(a-1,b)]
  if b>0: res+=[s+"B" for s in solve(a,b-1)]
  return res

while 1:
  try: a,b=map(int,input().split())
  except: break
  for s in sorted(solve(a,b)):
    print(s)