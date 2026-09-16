"""One fixed causal donor calibration; observation and replay are not a codec."""
import struct
Q=65536
M=1<<32

def rounded(n,d):
    return (n+d//2)//d

def clamp(c):return max(1,min(Q-1,c))

class Controller:
    def __init__(self,shifted=False):
        self.shifted=bool(shifted);self.clock=0;self.prefix=False;self.pending=None
        self.correct=[0]*8;self.total=[0]*8;self.weight=[M//2]*8
    def predict(self,c,flags,aligned,shifted):
        row=self.clock%8
        if self.pending is not None or not 1<=c<Q or flags&~15 or flags&7!=row:
            raise ValueError('prediction order or domain differs')
        if not row:self.prefix=bool(flags&8)
        donor=shifted if self.shifted else aligned
        bit=(donor>>(7-row))&1
        active=self.prefix
        q=c
        if active:
            confidence=clamp(rounded(Q*(2*self.correct[row]+1),2*self.total[row]+2))
            d=confidence if bit else Q-confidence
            q=clamp(rounded(self.weight[row]*c+(M-self.weight[row])*d,M))
        else:d=c
        self.pending=(c,d,bit,active,row)
        return q
    def observe(self,y):
        if self.pending is None or y not in (0,1):raise ValueError('observation order differs')
        c,d,bit,active,row=self.pending;self.pending=None
        if active:
            p=c if y else Q-c;v=d if y else Q-d;w=self.weight[row]
            self.weight[row]=max(1,min(M-1,rounded(M*w*p,w*p+(M-w)*v)))
            self.total[row]+=1;self.correct[row]+=int(y==bit)
            self.prefix &= y==bit
        self.clock+=1
    def state(self):
        if self.pending is not None:raise ValueError('pending prediction')
        return struct.pack('<Q?24Q',self.clock,self.prefix,*self.correct,*self.total,*self.weight)

def perfect_bound(hist):
    """Exact ceil of total ideal parent surprise on the eligible event set."""
    factors=[pow(c,n) for c,n in sorted(hist.items()) if n]
    if any(not 1<=c<Q or n<0 for c,n in hist.items()):raise ValueError('invalid histogram')
    while len(factors)>1:
        factors=[factors[i]*factors[i+1] if i+1<len(factors) else factors[i] for i in range(0,len(factors),2)]
    product=factors[0] if factors else 1
    return 16*sum(hist.values())-(product.bit_length()-1)
