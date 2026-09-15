# A paid sparse correction to the final coder

The dense512-byte correction remains retired on the exposed opening250KB:
its exact upper,including Q16 rounding, is less than173.304ideal byte-equivalents.
That bound does not rule out a different,explicitly paid parameter format.
This is one final sparse-pricing test of the same fixed hidden-feature map,
before considering different information sources. No native codec is rerun.

`fx2_sparse_residual_cost250k_v1` permits at most one nonzero coefficient per
bit-position row. Each row chooses one of32 retained causal ternary features and
an integer coefficient of magnitude1..16384 at scale32768. Parent state,features,
count denominator and rounding stay unchanged. Missing hidden features are zero.

The complete parameter table has versionbyte1,eight presence bits,and20bits per
active row: five feature-index bits,one sign bit,and14bits for magnitude-minus-one.
Finally pad with zero bits to a byte. Its total is

    K(k) = 8 ceil((16 + 20k)/8) bits, 0 <= k <= 8.

The table occupies2..22bytes. The earlier unrun sketch used a signed16-bit
coefficient,2..23bytes; before freezing,we removed its redundant zero code because
the mask already represents absent rows. All32768 nonzero coefficients now have
an exact15-bit code. Tests check every row mask,domain endpoints,padding and inverse.
Implementation,runtime and packaging multiplicities remain additional costs.

For one feature let x=phi*(y-p),G=sum(x),H=sum(x*x),and |a|<=1/2. The ideal gain
is F(a)=sum ln(1+a*x). Because |x|<=1,

    F''(a) = -sum x*x/(1+a*x)^2 <= -4H/9,
    F(a) <= aG - 2a*a*H/9.

The exact quadratic maximum occurs with the sign of G and magnitude
min(1/2,9|G|/(4H)); use zero when H=0. Its value is computed using integer first
and second moments and rational arithmetic. This upper covers every permitted
quantized coefficient; it does not assume the maximizing coefficient attains it.

Add the previously proved conservative Q16 rounding allowance per row. The row
allowance includes every event with any nonzero feature,so it also bounds events
for any particular selected feature. Convert to bits using a lower rational
bound for ln2. For each k, sum the k largest row upper bounds and subtract K(k).
Maximizing over all nine k values bounds every complete table,including padding.
This handles the cost interaction introduced by padding instead of pricing rows
independently and forgetting the final bytes.

Two independent bounded subprocesses must reproduce the exact certificate. They
rehash the native evidence,check encoder/decoder/repeat feature and coder identities,
verify raw and WRT inverses,check every truth coordinate,and independently match
the preceding gate's integer first moments. The native model is not executed;
the supplied features are research evidence,not free final decoder assets.

Seven tests cover5160 scalar objective comparisons,256 table masks,12800 joint
row-subset comparisons,malformed inputs,zero information and coefficient endpoints.
The discovery gate uses one CPU,1GiB memory,16MiB scratch and a360-second stop.
Resource or implementation failure is not a negative compression result.

A nonpositive exact paid upper rejects this entire sparse family under the
declared ideal-data-plus-table pricing on this population. A positive upper
permits a separate bounded fit and finite replay only. Neither result is a new
native archive,complete package,full-corpus projection or winning score. No table
encoding sweep follows a rejection under this gate. A later changed feature map
must identify the information it adds and carry its own evidence and cost.

The full objective remains90000000 complete bytes with exact canonical enwik9
reconstruction and independent eligibility evidence. Full-corpus score is unknown.
