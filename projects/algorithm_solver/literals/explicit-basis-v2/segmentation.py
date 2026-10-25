"""Independent code-point and byte DPs: selections, then characters, then IDs."""
def shortest_encode(text,vocabulary):
 if not vocabulary or any(not p for p in vocabulary) or len(set(vocabulary))!=len(vocabulary):raise ValueError('invalid dictionary')
 byfirst={}
 for index,piece in enumerate(vocabulary):byfirst.setdefault(piece[0],[]).append((index,piece))
 costs=[None]*(len(text)+1);choices=[None]*len(text);costs[-1]=(0,0)
 for at in range(len(text)-1,-1,-1):
  best=None
  for index,piece in byfirst.get(text[at],[]):
   end=at+len(piece)
   if text.startswith(piece,at) and costs[end] is not None:
    s,c=costs[end];candidate=(s+1,c+(len(piece)==1),index,end)
    if best is None or candidate<best:best=candidate
  if best is not None:costs[at]=best[:2];choices[at]=best[2:]
 if costs[0] is None:raise ValueError('source cannot be represented')
 result=[];at=0
 while at<len(text):index,at=choices[at];result.append(index)
 return result

def byte_encode(raw,vocabulary):
 # Forward recurrence is independent of the code-point/backward recurrence.
 # Persistent path tuples are bounded by the supplied complete source size.
 states=[None]*(len(raw)+1);states[0]=(0,0,());literals=[p.encode('utf8') for p in vocabulary];byfirst={}
 for i,p in enumerate(literals):byfirst.setdefault(p[0],[]).append((i,p))
 for at in range(len(raw)):
  state=states[at]
  if state is None:continue
  for index,piece in byfirst.get(raw[at],[]):
   if raw.startswith(piece,at):
    end=at+len(piece);candidate=(state[0]+1,state[1]+(len(vocabulary[index])==1),state[2]+(index,))
    if states[end] is None or candidate<states[end]:states[end]=candidate
 return None if states[-1] is None else list(states[-1][2])
