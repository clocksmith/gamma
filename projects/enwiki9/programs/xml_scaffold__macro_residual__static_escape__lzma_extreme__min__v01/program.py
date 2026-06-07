import lzma
P=9|lzma.PRESET_EXTREME
S=('<text xml:space="preserve">\1<mediawiki xmlns="http://www.mediawiki.org/xml/export-0.3/"\1 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\1 xsi:schemaLocation="http://www.mediawiki.org/xml/export-0.3/\1 http://www.mediawiki.org/xml/export-0.3.xsd"\1 version="0.3" xml:lang="en">\1  <siteinfo>\n\1  </siteinfo>\n\1    <namespaces>\n\1    </namespaces>\n\1  <page>\n\1  </page>\n\1    <title>\1</title>\n\1    <id>\1</id>\n\1    <revision>\n\1    </revision>\n\1      <id>\1      <timestamp>\1</timestamp>\n\1      <contributor>\n\1      </contributor>\n\1        <username>\1</username>\n\1        <id>\1      <minor />\n\1      <comment>\1</comment>\n\1      <text xml:space="preserve">\1</text>\n\1    <sitename>\1</sitename>\n\1    <base>\1</base>\n\1    <generator>\1</generator>\n\1    <case>\1</case>\n\1      <namespace key="0" />\n\1      <namespace key="\1</namespace>\n\1[[Category:\1{{\1}}\1[[\1]]\1&quot;\1&lt;\1&gt;\1&amp;').encode().split(b'\1')
A=sorted(enumerate(S,1),key=lambda p:-len(p[1]));D=dict(enumerate(S,1))
def _e(x):
 o=bytearray();i=0;n=len(x)
 while i<n:
  if x[i]==0:o+=b'\0\0';i+=1;continue
  for c,t in A:
   if x.startswith(t,i):o+=bytes((0,c));i+=len(t);break
  else:o.append(x[i]);i+=1
 return bytes(o)
def _d(x):
 o=bytearray();i=0;n=len(x)
 while i<n:
  b=x[i]
  if b:o.append(b);i+=1;continue
  if i+1>=n:raise ValueError('truncated')
  c=x[i+1];o+=D[c] if c else b'\0';i+=2
 return bytes(o)
def compress(x):
 r=b'R'+lzma.compress(x,preset=P);t=b'T'+lzma.compress(_e(x),preset=P)
 return t if len(t)<len(r) else r
def decompress(x):
 p=lzma.decompress(x[1:])
 if x[:1]==b'R':return p
 if x[:1]==b'T':return _d(p)
 raise ValueError('mode')
