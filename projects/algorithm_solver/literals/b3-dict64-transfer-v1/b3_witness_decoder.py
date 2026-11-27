"""Minimal standalone reference decoder for B3H1 witness packages (charged in complete_bits)."""
def rv(b,p):
 v=s=0
 while 1:
  x=b[p];p+=1;v|=(x&127)<<s
  if not x&128:return v,p
  s+=7
def decode_b3h1_witness(b):
 if len(b)<7 or b[:4]!=b"B3H1" or b[4]!=0:raise ValueError("hdr")
 n,p=rv(b,5)
 if not 1<=n<=64:raise ValueError("dict")
 d,seen=[],set()
 for _ in range(n):
  ln,p=rv(b,p);e=b[p:p+ln]
  if ln<1 or len(e)!=ln or e in seen:raise ValueError("entry")
  e.decode();seen.add(e);d.append(e);p+=ln
 ls=list(b[p:p+n+1]);p+=n+1
 if len(ls)!=n+1 or min(ls)<1 or max(ls)>32:raise ValueError("len")
 t=max(ls)
 if sum(1<<(t-x)for x in ls)!=1<<t:raise ValueError("kraft")
 ht,c,pv={},0,None
 for s in sorted(range(n+1),key=lambda i:(ls[i],i)):
  l=ls[s];c=0 if pv is None else(c+1)<<(l-pv);pv=l;ht[(l,c)]=s
 nf,p=rv(b,p);out,bp,tb=[],p*8,len(b)*8
 for _ in range(nf):
  u,c,l=bytearray(),0,0
  while 1:
   if bp>=tb:raise ValueError("eof")
   c=(c<<1)|((b[bp>>3]>>(7-(bp&7)))&1);bp+=1;l+=1;s=ht.get((l,c))
   if s is not None:
    c=l=0
    if s==n:break
    u.extend(d[s])
  out.append(u.decode())
 if tb-bp>=8:raise ValueError("trail")
 while bp<tb:
  if(b[bp>>3]>>(7-(bp&7)))&1:raise ValueError("pad")
  bp+=1
 return d,out
