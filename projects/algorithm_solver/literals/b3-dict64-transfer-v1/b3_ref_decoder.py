"""Minimal standalone reference decoder for B3H1 packages (charged in complete_bits)."""
def rv(b,p):
 v=s=0
 while 1:
  x=b[p];p+=1;v|=(x&127)<<s
  if not x&128:return v,p
  s+=7
def hf(ls):
 if not ls or min(ls)<1 or max(ls)>32:raise ValueError("len")
 t=max(ls)
 if sum(1<<(t-x)for x in ls)!=1<<t:raise ValueError("kraft")
 d,c,pv={},0,None
 for s in sorted(range(len(ls)),key=lambda i:(ls[i],i)):
  l=ls[s];c=0 if pv is None else(c+1)<<(l-pv);pv=l;d[(l,c)]=s
 return d
def decode_b3h1(b):
 if len(b)<7 or b[:4]!=b"B3H1":raise ValueError("magic")
 fm,p=b[4],5
 if fm not in(0,1,2):raise ValueError("mode")
 n,p=rv(b,p)
 if not 1<=n<=64:raise ValueError("dict")
 d,seen=[],set()
 for _ in range(n):
  ln,p=rv(b,p);e=b[p:p+ln]
  if ln<1 or len(e)!=ln or e in seen:raise ValueError("entry")
  e.decode();seen.add(e);d.append(e);p+=ln
 ls=list(b[p:p+n+1])
 if len(ls)!=n+1:raise ValueError("tbl")
 p+=n+1;ht=hf(ls);fb=None
 if fm==2:
  nb,p=rv(b,p);fb=[bytes([x])for x in b[p:p+nb]];p+=nb;nm,p=rv(b,p)
  for _ in range(nm):fb.append(fb[b[p]]+fb[b[p+1]]);p+=2
 nf,p=rv(b,p);ms=[0]*nf
 if fm:sb=(nf+7)//8;sr=b[p:p+sb];p+=sb;ms=[(sr[k>>3]>>(7-(k&7)))&1 for k in range(nf)]
 out,bp,tb=[],p*8,len(b)*8
 for m in ms:
  if not m:
   u,c,l=bytearray(),0,0
   while 1:
    if bp>=tb:raise ValueError("eof")
    c=(c<<1)|((b[bp>>3]>>(7-(bp&7)))&1);bp+=1;l+=1;s=ht.get((l,c))
    if s is not None:
     c=l=0
     if s==n:break
     u.extend(d[s])
   out.append(u.decode())
  else:
   if bp&7:
    r=8-(bp&7)
    if b[bp>>3]&((1<<r)-1):raise ValueError("pad")
    bp+=r
   p=bp>>3
   if fm==1:ln,p=rv(b,p);out.append(b[p:p+ln].decode());p+=ln
   else:
    nt,p=rv(b,p);u,ec=bytearray(),len(fb)
    for _ in range(nt):
     s=b[p];p+=1
     if s==ec:u.append(b[p]);p+=1
     else:u.extend(fb[s])
    out.append(u.decode())
   bp=p*8
 if tb-bp>=8:raise ValueError("trail")
 while bp<tb:
  if(b[bp>>3]>>(7-(bp&7)))&1:raise ValueError("pad")
  bp+=1
 return d,out,ms
