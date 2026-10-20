import itertools,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from search import trie,encode_text,structural_groups
sys.path.insert(0,sys.argv[1] if len(sys.argv)>1 else str(Path(__file__).resolve().parents[1]))
from literals import shortest_encode
count=0
for vocab in [['a','ab','bc'],['a','b','aa','ab','ba','bb'],['ab','ba','aba','b']]:
 for n in range(1,7):
  for chars in itertools.product('ab',repeat=n):
   text=''.join(chars)
   try:expected=shortest_encode(text,vocab)
   except ValueError:
    try:encode_text(text,trie(vocab))
    except ValueError:pass
    else:raise AssertionError('Representation disagreement')
   else:assert encode_text(text,trie(vocab))==expected
   count+=1
assert encode_text('abc',trie(['a','ab','bc']))==[0,2]
groups,history=structural_groups({i:{str(i%2),str(i)} for i in range(8)});assert len(groups)==4 and set.union(*groups)==set(range(8))
print(count,'exact segmentation parity cases plus greedy-counterexample and cluster-coverage checks passed')
