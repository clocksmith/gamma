"""Paid one-coordinate-per-row corrections and exact curvature bounds."""
from fractions import Fraction
import struct
from lib.fx2_residual_projection_v1 import Q, RADIUS, certificate, ln2_bounds, rational, unpack


def quadratic_upper(sum_v, sum_v2):
    """v=Q*x. F(a)<=a*G-2*a*a*H/9 for every |a|<=1/2."""
    if not isinstance(sum_v,int) or not isinstance(sum_v2,int) or sum_v2<0:
        raise ValueError('invalid moments')
    if not sum_v2:
        if sum_v:raise ValueError('inconsistent zero second moment')
        return Fraction()
    g=abs(sum_v)
    if 9*Q*g<=2*sum_v2:
        return Fraction(9*g*g,8*sum_v2)
    return Fraction(g,2*Q)-Fraction(sum_v2,18*Q*Q)


def table_bits(active_rows):
    if not isinstance(active_rows,int) or not 0<=active_rows<=8:
        raise ValueError('invalid active row count')
    return 8*((16+20*active_rows+7)//8)


def pack(rows):
    if len(rows)!=8:raise ValueError('eight rows required')
    mask=0;entries=[]
    for r,row in enumerate(rows):
        if row is None:continue
        j,k=row
        if not isinstance(j,int) or not isinstance(k,int) or not 0<=j<32 or not 0<abs(k)<=RADIUS:
            raise ValueError('invalid sparse coefficient')
        mask|=1<<(7-r);entries.append((j,k))
    value=(1<<8)|mask;bits=16
    for j,k in entries:
        code=(int(k<0)<<14)|(abs(k)-1)
        value=(value<<20)|(j<<15)|code;bits+=20
    size=(bits+7)//8;value<<=size*8-bits
    return value.to_bytes(size,'big')


def unpack_table(data):
    if len(data)<2 or data[0]!=1:raise ValueError('invalid table version/header')
    mask=data[1];active=mask.bit_count();expected=table_bits(active)//8
    if len(data)!=expected:raise ValueError('invalid table extent')
    bits=16+20*active;padding=len(data)*8-bits;value=int.from_bytes(data,'big')
    if value&((1<<padding)-1):raise ValueError('nonzero table padding')
    value>>=padding;rows=[];left=20*active
    for r in range(8):
        if not mask&(1<<(7-r)):rows.append(None);continue
        left-=20;entry=(value>>left)&((1<<20)-1);j=entry>>15;code=entry&32767
        k=((code&16383)+1)*(-1 if code&16384 else 1)
        rows.append((j,k))
    if pack(rows)!=data:raise ValueError('noncanonical table')
    return rows


def paid_upper(row_upper_bits):
    if len(row_upper_bits)!=8 or any(v<0 for v in row_upper_bits):
        raise ValueError('eight nonnegative row bounds required')
    ordered=sorted(enumerate(row_upper_bits),key=lambda r:(-r[1],r[0]))
    choices=[];total=Fraction()
    for k in range(9):
        if k:total+=ordered[k-1][1]
        bound=total-table_bits(k)
        choices.append(dict(active_rows=k,selected_upper_bound_rows=[r for r,_ in ordered[:k]],
            table_bytes=table_bits(k)//8,paid_upper_bits=rational(bound),
            paid_upper_bits_diagnostic=float(bound)))
    best=max(range(9),key=lambda k:Fraction(int(choices[k]['paid_upper_bits']['numerator']),int(choices[k]['paid_upper_bits']['denominator'])))
    return choices,best


def analyze(features,body,coder):
    base=certificate(features,body,coder)
    squares=[[0]*32 for _ in range(8)];hist=[[0]*Q for _ in range(8)]
    last=None;phi=None
    for i,(packed,c,flags,y) in enumerate(struct.iter_unpack('<QHBB',features)):
        if not packed:continue
        if packed!=last:phi=unpack(packed);last=packed
        v=Q*y-c;v2=v*v;row=squares[i%8]
        for j,x in enumerate(phi):
            if x:row[j]+=v2
        hist[i%8][c if y else Q-c]+=1
    loglo,_=ln2_bounds();scale=1<<48;rows=[];smooth=[];rounded=[]
    for r in range(8):
        per_feature=[quadratic_upper(g,h) for g,h in zip(base['residual_integer_sums'][r],squares[r])]
        j=max(range(32),key=lambda j:per_feature[j])
        rounding=Fraction(sum((n*Q*scale+c*(Q+c)-1)//(c*(Q+c)) for c,n in enumerate(hist[r]) if n),scale)
        smooth.append(per_feature[j]/loglo);rounded.append((per_feature[j]+rounding)/loglo)
        rows.append(dict(bit_position=r,best_bound_feature=j,
            feature_upper_nats=[rational(v) for v in per_feature],
            rounding_upper_nats=rational(rounding),smooth_upper_bits=rational(smooth[-1]),
            rounded_upper_bits=rational(rounded[-1]),rounded_upper_bits_diagnostic=float(rounded[-1])))
    plans,best=paid_upper(rounded);smooth_plans,smooth_best=paid_upper(smooth)
    upper=plans[best]['paid_upper_bits']
    may_fit=int(upper['numerator'])>0
    return dict(schema='gamma.enwiki9.sparse-residual-curvature.v1',events=base['events'],
        raw_population='[0,250000)',residual_integer_sums=base['residual_integer_sums'],
        residual_integer_squares=squares,rows=rows,paid_options=plans,
        smooth_paid_options=smooth_plans,best_bound_active_rows=best,
        smooth_best_bound_active_rows=smooth_best,paid_upper_bits=upper,
        paid_upper_bits_diagnostic=plans[best]['paid_upper_bits_diagnostic'],
        fitting_permitted_by_bound=may_fit,table_min_bytes=2,table_max_bytes=22,
        finite_archive_bound=False,coefficients_fitted=False,
        complete_package_bytes=None,full_corpus_score_bytes=None,objective_credit_bytes=0)
