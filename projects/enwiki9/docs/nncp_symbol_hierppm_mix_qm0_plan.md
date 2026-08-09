# NNCP Mature Symbol Hierarchical PPM Mixture QM0

Status: frozen same-domain causal codelength screen; zero score credit.

## Question

Does a decoder-built symbol PPM expose mature predictive information absent
from the exact NNCP v3.3 distribution? The experiment consumes the complete
receipt-bound trace through execution row 1,998,848 and scores only the causally
closed final native block `[1,499,136, 1,998,848)`.

## Model

Derive the native block, stream, and local position from the trace's original
symbol ordinal and verify the exact state-major execution schedule. Maintain
global symbol counts and separate histories for the 32 native streams. The
normalized hierarchy is:

```text
P0(a)       = (n(a)+1/2) / (N+V/2)
P1(a|b)     = (n(b,a)+16 P0(a)) / (n(b)+16)
P2(a|b,c)   = (n(b,c,a)+8 P1(a|c)) / (n(b,c)+8)
```

Mix each expert with the exact NNCP symbol probability through a two-expert
Bayesian posterior. Each stream resets to equal prior at the existing
64-symbol update boundary. Both probabilities are over the same complete
16,392-symbol alphabet; updates occur only after truth.

Controls are order zero, stream order one, and execution-order order one. The
last control preserves pair-table capacity while replacing the actual
within-stream predecessor with the immediately preceding symbol executed on a
different stream.

## Gate

The stream-order-2 mixture must save at least 7,000 ideal bytes on the frozen
499,712-symbol mature block, remain positive in every chronological third, and
beat both stream-order-1 and execution-order-1 mixtures by at least 1,000
bytes. Compressed diagnostic source must not exceed 65,536 bytes.

A pass authorizes a separately frozen finite arithmetic stream. A miss retires
this context order, concentrations, native-stream partition, and switching
schedule without parameter sweeps. This shadow cannot inherit the published
NNCP score and produces no forecast or score credit.
