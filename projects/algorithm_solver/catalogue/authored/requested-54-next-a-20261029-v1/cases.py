"""Small brute-reference scenarios and analytic boundaries are separate."""
import random
from itertools import product
IDS=[834,842,850,857,879,880]
def small_cases():
 rng=random.Random(834842)
 for n in range(1,16):
  for _ in range(10):yield 834,[n,[[i,rng.randrange(i)] for i in range(1,n)]]
 for n in range(1,7):
  for chars in product('012',repeat=n):yield 842,[''.join(chars)]
 for s in ['1101111','112358130','123456579','214748364721474836420']:
  yield 842,[s]
 for _ in range(150):
  rects=[]
  for _ in range(rng.randrange(1,8)):
   a,c=sorted(rng.sample(range(7),2));b,d=sorted(rng.sample(range(7),2));rects.append([a,b,c,d])
  yield 850,[rects]
 for _ in range(160):
  n=rng.randrange(1,9);yield 857,[[rng.randrange(1,21) for _ in range(n)],[rng.randrange(1,31) for _ in range(n)],rng.randrange(1,n+1)]
 for _ in range(180):
  c=rng.randrange(1,10);yield 879,[rng.randrange(1,12),rng.randrange(11),[rng.randrange(1,8) for _ in range(c)],[rng.randrange(8) for _ in range(c)]]
 for _ in range(180):
  s=rng.choice('abc');length=1
  for _ in range(rng.randrange(1,8)):
   ch=rng.choice('abc23');s+=ch;length=length*int(ch) if ch.isdigit() else length+1
  yield 880,[s,rng.randrange(1,length+1)]
def boundary_cases():
 n=30000
 yield 834,[n,[[i-1,i] for i in range(1,n)]],[i*(i+1)//2+(n-1-i)*(n-i)//2 for i in range(n)],'Chain distance sums are triangular numbers on each side.'
 yield 834,[n,[[0,i] for i in range(1,n)]],[n-1]+[2*n-3]*(n-1),'Star center distance one to each leaf, leaf distance two to all other leaves.'
 yield 842,['0'*200],True,'Maximum-length zero string splits into200 valid zero terms; compare witness directly.'
 yield 842,['9'*200],[],'Any nonzero term has at most10 digits; equal leading 9 digits cannot follow the sum of preceding positive leading-9 terms to produce a 200-digit valid split.'
 yield 850,[[[0,0,10**9,10**9]]*200],49,'Maximum count and coordinate extent, all identical; union area1e18 mod1e9+7=49.'
 yield 850,[[[i*5000000,0,(i+1)*5000000,10**9] for i in range(200)]],49,'200 disjoint strips tile the same1e9 square.'
 yield 857,[[10000]*10000,[10000]*10000,10000],100000000.0,'All10000 workers hired at ratio one.'
 yield 857,[[1]*10000,[10000]*10000,1],10000.0,'One of10000 equal workers costs its exact minimum wage.'
 yield 879,[100,100,[1]*100,[100]*100],(pow(2,100,1000000007)-1)%1000000007,'Every nonempty subset fits and earns at least100.'
 yield 879,[100,0,[1]*100,[0]*100],pow(2,100,1000000007),'All subsets including empty fit with zero required profit.'
 yield 879,[100,100,[100]*100,[100]*100],100,'Only singleton crime subsets fit; each earns100.'
 yield 880,['a'*99+'2',198],'a','Maximum encoded length100; decoded tape contains only a.'
 yield 880,['a'+'9'*19,10**9],'a','9^19<2^63; a-only tape covers maximum k exactly.'
