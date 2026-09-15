"""Exact core and conservative certificates for the declared affine family."""
from fractions import Fraction
import struct

Q=65536
S=32768
RADIUS=S//2
COEFFICIENT_BYTES=512

def count(c,k):
    if not (isinstance(c,int) and isinstance(k,int) and 1<=c<Q and abs(k)<=RADIUS):
        raise ValueError('invalid count or correction')
    den=Q*S
    return max(1,min(Q-1,(c*den+c*(Q-c)*k+den//2)//den))

def unpack(packed):
    if not 0<=packed<1<<64: raise ValueError('feature width')
    result=[]
    for j in range(32):
        v=(packed>>(2*j))&3
        if v==3: raise ValueError('invalid ternary code')
        result.append((0,1,-1)[v])
    return result

def ln2_bounds(terms=32):
    # ln(2)=2*atanh(1/3); bound positive tail by its geometric majorant.
    if terms<1: raise ValueError('positive term count required')
    lower=2*sum((Fraction(1,(2*i+1)*3**(2*i+1)) for i in range(terms)),Fraction())
    upper=lower+Fraction(2,3**(2*terms+1)*(2*terms+1))*Fraction(9,8)
    return lower,upper

def rational(v): return dict(numerator=str(v.numerator),denominator=str(v.denominator))

def bounds(rows):
    """Rows (p,y,phi); ideal natural-log bounds for one fixed coefficient row."""
    sums=[0]*32; data=[]
    for p,y,phi in rows:
        if not 1<=p<Q or y not in (0,1) or len(phi)!=32 or any(v not in (-1,0,1) for v in phi):
            raise ValueError('invalid event')
        x=[v*(Q*y-p) for v in phi];data.append(x)
        sums=[a+b for a,b in zip(sums,x)]
    upper=Fraction(max(map(abs,sums),default=0),2*Q)
    return upper,data

def lower_bound(data,coefficients):
    if len(coefficients)!=32 or any(not isinstance(k,int) for k in coefficients) or sum(map(abs,coefficients))>RADIUS:
        raise ValueError('coefficient L1 domain')
    answer=Fraction()
    for row in data:
        z=Fraction(sum(a*b for a,b in zip(coefficients,row)),Q*S)
        if abs(z)>Fraction(1,2): raise ValueError('domain violation')
        answer+=z-z*z
    return answer

def certificate(trace,modeled,coder):
    """No fitting. Trace identity and exact zero-point upper bounds on all8rows."""
    if len(trace)!=len(modeled)*8*12 or len(coder)!=len(modeled)*8*28:
        raise ValueError('population framing differs')
    sums=[[0]*32 for _ in range(8)]
    hist=[0]*Q; active=0;valid=0;last_packed=None;phi=None
    for i,((packed,c,flags,y),base) in enumerate(zip(struct.iter_unpack('<QHBB',trace),struct.iter_unpack('<7I',coder))):
        if flags&~15 or flags&7!=i%8 or y!=((modeled[i//8]>>(7-i%8))&1):
            raise ValueError('feature clock/truth differs')
        if not 1<=c<Q or (c,y)!=(base[1],base[6]): raise ValueError('actual coder count differs')
        if not flags&8 and packed: raise ValueError('missing feature not zero')
        if i%8 and (packed,flags&8)!=previous: raise ValueError('features changed within byte')
        previous=(packed,flags&8)
        valid+=bool(flags&8)
        if packed!=last_packed: phi=unpack(packed);last_packed=packed
        if not packed: continue
        active+=1;hist[c if y else Q-c]+=1
        residual=Q*y-c;row=sums[i%8]
        for j,v in enumerate(phi): row[j]+=v*residual
    maxima=[max(map(abs,row)) for row in sums]
    ideal=Fraction(sum(maxima),2*Q)
    # q_truth >= c_truth*(Q+c_truth)/(2Q) count units. Rounding/clamping
    # raises count by at most1/2, hence ln(q_round/q)<=Q/[c_truth*(Q+c_truth)].
    # Round each histogram term upward on a shared2^-48 grid: exact upper.
    scale=1<<48
    rounding=Fraction(sum((n*Q*scale+c*(Q+c)-1)//(c*(Q+c)) for c,n in enumerate(hist) if n),scale)
    loglo,loghi=ln2_bounds()
    ideal_bits=ideal/loglo;rounded_bits=(ideal+rounding)/loglo
    return dict(schema='gamma.enwiki9.residual-affine-bound.v1',events=len(modeled)*8,
        valid_feature_events=valid,nonzero_feature_events=active,rows=8,features_per_row=32,
        residual_integer_sums=sums,max_abs_sums=maxima,coefficient_bytes=COEFFICIENT_BYTES,
        ideal_upper_nats=rational(ideal),rounding_upper_nats=rational(rounding),
        ln2_lower=rational(loglo),ln2_upper=rational(loghi),
        ideal_upper_bits=rational(ideal_bits),rounded_upper_bits=rational(rounded_bits),
        ideal_upper_bits_diagnostic=float(ideal_bits),rounded_upper_bits_diagnostic=float(rounded_bits),
        ideal_can_pay_coefficients=ideal_bits>8*COEFFICIENT_BYTES,
        rounded_can_pay_coefficients=rounded_bits>8*COEFFICIENT_BYTES,
        finite_archive_bound=False,complete_package_bytes=None,objective_credit_bytes=0)
