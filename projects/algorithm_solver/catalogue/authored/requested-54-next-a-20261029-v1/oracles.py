"""Independent small-domain references; no candidate imports or language agreement."""
from collections import deque
from itertools import combinations
from fractions import Fraction

def validate_domain(pid,args):
 def integer(x,a,b):assert type(x) is int and a<=x<=b
 if pid==834:
  n,edges=args;integer(n,1,30000);assert len(edges)==n-1
  parent=list(range(n))
  def find(x):
   while parent[x]!=x:x=parent[x]
   return x
  for a,b in edges:
   integer(a,0,n-1);integer(b,0,n-1);assert a!=b
   x,y=find(a),find(b);assert x!=y;parent[x]=y
 elif pid==842:
  s,=args;assert type(s) is str and 1<=len(s)<=200 and s.isascii() and s.isdigit()
 elif pid==850:
  rectangles,=args;integer(len(rectangles),1,200)
  for x,y,a,b in rectangles:
   for v in [x,y,a,b]:integer(v,0,10**9)
   assert x<a and y<b
 elif pid==857:
  q,w,k=args;assert len(q)==len(w);integer(len(q),1,10000);integer(k,1,len(q))
  for x in q+w:integer(x,1,10000)
 elif pid==879:
  n,p,g,profit=args;integer(n,1,100);integer(p,0,100);assert len(g)==len(profit);integer(len(g),1,100)
  for x in g:integer(x,1,100)
  for x in profit:integer(x,0,100)
 elif pid==880:
  s,k=args;assert 2<=len(s)<=100 and 'a'<=s[0]<='z';integer(k,1,10**9);length=0
  for ch in s:
   assert 'a'<=ch<='z' or ch in '23456789'
   length=length*int(ch) if ch.isdigit() else length+1
  assert k<=length<2**63
 else:raise ValueError(pid)

def reference(pid,args):
 validate_domain(pid,args)
 if pid==834:
  n,edges=args;g=[[] for _ in range(n)]
  for a,b in edges:g[a].append(b);g[b].append(a)
  out=[]
  for start in range(n):
   d={start:0};q=deque([start])
   while q:
    u=q.popleft()
    for v in g[u]:
     if v not in d:d[v]=d[u]+1;q.append(v)
   out.append(sum(d.values()))
  return out
 if pid==842:
  s,=args;answers=[]
  def visit(i,parts):
   if i==len(s):
    if len(parts)>=3:answers.append(parts)
    return
   for j in range(i+1,min(len(s),i+10)+1):
    text=s[i:j]
    if len(text)>1 and text[0]=='0':break
    value=int(text)
    if value>=2**31:break
    if len(parts)>=2 and value!=parts[-1]+parts[-2]:continue
    visit(j,parts+[value])
  visit(0,[]);return answers
 if pid==850:
  rects,=args
  return len({(x,y) for a,b,c,d in rects for x in range(a,c) for y in range(b,d)})%1000000007
 if pid==857:
  quality,wage,k=args
  return float(min(sum(quality[i] for i in group)*max(Fraction(wage[i],quality[i]) for i in group) for group in combinations(range(len(quality)),k)))
 if pid==879:
  n,p,g,profit=args
  return sum(sum(g[i] for i in range(len(g)) if mask>>i&1)<=n and sum(profit[i] for i in range(len(g)) if mask>>i&1)>=p for mask in range(1<<len(g)))%1000000007
 if pid==880:
  s,k=args;tape=''
  for ch in s:tape=tape*int(ch) if ch.isdigit() else tape+ch
  return tape[k-1]
 raise ValueError(pid)

def compare(pid,args,actual,expected):
 if pid==842:
  if not actual:return expected==[]
  return type(actual) is list and len(actual)>=3 and all(type(x) is int and 0<=x<2**31 for x in actual) and ''.join(map(str,actual))==args[0] and all(actual[i]+actual[i+1]==actual[i+2] for i in range(len(actual)-2))
 if pid==857:return type(actual) in (int,float) and abs(actual-expected)<=1e-5
 return type(actual) is type(expected) and actual==expected
