# NNCP Dictionary-Boundary Class Marginal QM0

Candidate: `nncp_dictionary_boundary_class_marginal_qm0_v1`

Status: frozen archive-neutral full-distribution screen; zero score credit.

## Question

Can the already-counted NNCP dictionary define a causal symbol-class marginal
that predicts information absent from NNCP's exact symbol distribution?

The screen uses the receipt-bound opening `10,000`-symbol full-distribution
trace.  It does not condition on the unknown target class.  For every symbol
expansion, the decoder derives one class from:

```text
category(first expansion byte)
category(last expansion byte)
ceil(log2(expansion length))
```

The six byte categories are ASCII letter, digit, whitespace, selected
punctuation, control/non-ASCII, and other ASCII.  Rounded unused vocabulary
leaves receive distinct dummy classes.

## Legal model

For NNCP probability `B(s)`, class mass `B(c)`, last-32 same-stream class count
`n(c)`, and window population `N`, define:

```text
D(s) = ((n(c(s)) + 16 B(c(s))) / (N + 16)) * B(s) / B(c(s))
P(s) = (16 B(s) + D(s)) / 17
```

Thus the class marginal adapts while NNCP's exact conditional distribution
inside the class is preserved.  Counts update only after truth.  The matched
control rotates the complete symbol-to-class map by 37 IDs while preserving
the same probability formula and state capacity.

## Gate

Require at least `250` ideal bytes over exact NNCP on `10,000` symbols,
positive chronological thirds, and at least `100` bytes over the rotated-map
control.  Compressed diagnostic source must not exceed `65,536` bytes.

A pass authorizes one independently terminated native same-object gate that
computes class masses directly from NNCP's full probability table.  A miss
retires this exact boundary-class definition, last-32 marginal, concentrations,
and rotated control without class, window, or prior sweeps.  This screen cannot
inherit an NNCP archive, package, forecast, eligibility, or score claim.
