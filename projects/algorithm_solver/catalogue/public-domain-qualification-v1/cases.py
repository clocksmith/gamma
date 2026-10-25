"""Public synthetic foundation cases; no private cases or candidate oracle."""
import itertools,json
from pathlib import Path
from oracle import IDS,expected,exact,validate

def build(directory):
 result={}
 for pid in IDS:
  supplied=json.loads((Path(directory)/f'{pid}.cases.json').read_bytes());rows=[]
  for case in supplied['cases']:
   want=expected(pid,case['args'])
   if not exact(want,case['expected'])and not(pid==916 and sorted(want)==sorted(case['expected'])):raise ValueError('independent supplied expectation disagrees')
   rows.append({'args':case['args'],'expected':want,'origin':'independent-public-contract-author','purpose':case['purpose']})
  result[pid]=rows
 def add(pid,args,purpose):result[pid].append({'args':args,'expected':expected(pid,args),'origin':'deterministic-public-domain-generator','purpose':purpose})
 for n in range(1,13):
  a=[-30+3*i for i in range(n)]
  for pivot in range(n):add(153,[a[pivot:]+a[:pivot]],'all small rotations')
 a=list(range(-2500,2500))
 for pivot in (0,1,2499,4999):add(153,[a[pivot:]+a[:pivot]],'maximum length rotation')
 for n in range(2,9):
  for missing in range(1,n+1):
   for duplicate in range(1,n+1):
    if duplicate!=missing:
     a=list(range(1,n+1));a[missing-1]=duplicate
     add(645,[a if (missing+duplicate)%2 else a[::-1]],'all small duplicate/missing pairs')
 for missing,duplicate in ((1,10000),(10000,1)):
  a=list(range(1,10001));a[missing-1]=duplicate;add(645,[a],'maximum length missing/duplicate extremes')
 for n in range(1,7):
  for a in itertools.product((-1,0,1),repeat=n):add(674,[list(a)],'exhaustive small ternary arrays')
 for a in (list(range(10000)),list(range(10000,0,-1)),[7]*10000):add(674,[a],'maximum length monotonic/constant boundary')
 for n in (1,2,3):
  for flat in itertools.product((0,1),repeat=n*n):add(832,[[list(flat[i*n:(i+1)*n])for i in range(n)]],'exhaustive small binary matrices')
 for a in ([[0]*20 for _ in range(20)],[[1]*20 for _ in range(20)],[[int((i*3+j*7)%5<2)for j in range(20)]for i in range(20)]):add(832,[a],'maximum square boundary')
 add(833,['a'*1000,list(range(0,1000,10)),['a']*100,['b'*50]*100],'maximum length/count/target expansion')
 add(833,['a'*1000,[950,0],['a'*50]*2,['b','c']],'length50 source at both ends, unsorted simultaneous edits')
 for source in ('abcd','abca','aaaa'):
  for indices in ([0,2],[2,0]):add(833,[source,indices,[source[i]for i in indices],['xy','z']],'nonoverlap unsorted length changes')
 words=['a','b','aa','ab','ba','abb','baa','bba','abc','cccccccccc']
 for req in (['a'],['a','a'],['aa'],['a','b'],['ab','aa'],['cccccccccc'],['z']):add(916,[words,list(req)],'independent multiplicity and duplicate requirements')
 words=[''.join(chr(97+(i//26**j)%26)for j in range(4))for i in range(10000)]
 add(916,[words,['a']*10000],'maximum distinct words and repeated requirements')
 for pid,rows in result.items():
  for row in rows:validate(pid,row['args'])
 return result
