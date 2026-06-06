import lzma
T=b'<text xml:space="preserve">\x00</text>\x00<page>\x00</page>\x00<revision>\x00</revision>\x00<contributor>\x00</contributor>\x00<timestamp>\x00</timestamp>\x00<username>\x00</username>\x00<comment>\x00</comment>\x00<title>\x00</title>\x00<id>\x00</id>\x00<minor />\x00{{\x00}}\x00[[Category:\x00[[Image:\x00[[\x00]]\x00&quot;\x00&lt;\x00&gt;\x00&amp;\x00http://\x00https://\x00<ref\x00</ref>\x00|thumb\x00|right\x00|left\x00Category:\x00File:\x00Image:'.split(b'\x00')
B=sorted(enumerate(T,1),key=lambda x:-len(x[1]))
D=dict(enumerate(T,1))
def _e(d):
 o=bytearray();i=0;n=len(d)
 while i<n:
  if d[i]==0:o+=b'\x00\xff';i+=1;continue
  for c,t in B:
   if d.startswith(t,i):o+=bytes((0,c));i+=len(t);break
  else:o.append(d[i]);i+=1
 return bytes(o)
def _d(s):
 o=bytearray();i=0;n=len(s)
 while i<n:
  b=s[i]
  if b!=0:o.append(b);i+=1;continue
  c=s[i+1]
  o.append(0) if c==255 else o.extend(D[c])
  i+=2
 return bytes(o)
def compress(d):return lzma.compress(_e(d),preset=9|lzma.PRESET_EXTREME)
def decompress(d):return _d(lzma.decompress(d))
