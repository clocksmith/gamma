import lzma
T=b"""<text xml:space="preserve">
</text>
<page>
</page>
<revision>
</revision>
<contributor>
</contributor>
<timestamp>
</timestamp>
<username>
</username>
<comment>
</comment>
<title>
</title>
<id>
</id>
<minor />
{{
}}
[[Category:
[[Image:
[[
]]
&quot;
&lt;
&gt;
&amp;
http://
https://
<ref
</ref>
|thumb
|right
|left
Category:
File:
Image:""".splitlines()
S=sorted(enumerate(T,1),key=lambda x:-len(x[1]))
D=dict(enumerate(T,1))
F=[{"id":lzma.FILTER_LZMA2,"preset":9|lzma.PRESET_EXTREME,"dict_size":1<<30}]
def E(d):
 o=bytearray();i=0;n=len(d)
 while i<n:
  if d[i]==0:o+=b"\0\xff";i+=1;continue
  for c,t in S:
   if d.startswith(t,i):o+=bytes((0,c));i+=len(t);break
  else:o.append(d[i]);i+=1
 return bytes(o)
def R(d):
 o=bytearray();i=0;n=len(d)
 while i<n:
  if d[i]:o.append(d[i]);i+=1;continue
  c=d[i+1];o+=b"\0" if c==255 else D[c];i+=2
 return bytes(o)
def compress(d):return lzma.compress(E(d),format=lzma.FORMAT_XZ,filters=F)
def decompress(d):return R(lzma.decompress(d))
