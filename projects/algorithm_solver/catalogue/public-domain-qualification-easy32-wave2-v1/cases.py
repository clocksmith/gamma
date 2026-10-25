"""Synthetic bounded exhaustive-small and boundary fixtures."""
from itertools import product
from oracle import IDS,expected

def build(_public=None):
 out={i:[]for i in IDS};seen={i:set()for i in IDS}
 def add(pid,args):
  key=repr(args)
  if key not in seen[pid]:seen[pid].add(key);out[pid].append({'args':args,'expected':expected(pid,args)})
 for words in product(('a','b','c','aa','ab','ba','bb','ij','ja'),repeat=3):add(1880,list(words))
 for words in(['j'*8,'a','j'*8],['j'*8,'b','a'*8],['a'*8,'a'*8,'a'*8]):add(1880,words)
 intervals=[[a,b]for a in range(1,4)for b in range(a,4)]
 for count in(1,2):
  for rs in product(intervals,repeat=count):
   for l in range(1,4):
    for r in range(l,4):add(1893,[[list(x)for x in rs],l,r])
 add(1893,[[[i,i]for i in range(1,51)],1,50]);add(1893,[[[1,1]]*50,1,50])
 for n in range(1,4):
  for ws in product(('a','b','aa','ab','ba','bb'),repeat=n):add(1897,[list(ws)])
 for ws in(['a'*100]*100,['a'*99+'b']*100,['a'*100]*99+['a'*99+'b']):add(1897,[ws])
 for n in list(range(1,501))+[x*x for x in range(23,101)]+[9999,10000]:add(1952,[n])
 for n in range(1,6):
  for chars in product('ab',repeat=n):
   for ch in 'abc':add(2000,[''.join(chars),ch])
 add(2000,['a'*249+'z','z']);add(2000,['z'*250,'a'])
 for n in range(1,5):
  for ops in product(('++X','X++','--X','X--'),repeat=n):add(2011,[list(ops)])
 add(2011,[['++X']*100]);add(2011,[['--X']*100])
 for n in range(3,6):
  for xs in product((0,1,2),repeat=n):add(2094,[list(xs)])
 for xs in([0]*100,[1]*100,list(range(10))*10,[2]*100,[8,8,2]*33+[8]):add(2094,[xs])
 for n in range(1,4):
  for ws in product(('a','ab','aa','aba','abb'),repeat=n):add(2108,[list(ws)])
 add(2108,[['ab'*50]*99+['a'*100]]);add(2108,[['ab'*50]*100])
 return out
