# QH-1: Observable Heading-State Prediction

## Problem

Let a reversible encoded stream reconstruct raw text through deterministic
emission groups. A line automaton reads only raw bytes released by completed
groups. When a complete heading line is observed, a fixed classifier maps it
to one of finitely many states; that state remains active until the next
heading or page boundary.

An auxiliary finite predictor is keyed by:

1. the active heading state;
2. a fixed suffix of already decoded encoded symbols;
3. the current partial encoded symbol.

Prove:

1. Heading-state transitions occur at identical encoded boundaries for the
   encoder and decoder.
2. The active state before every encoded bit depends only on decoded history.
3. A finite count predictor updated after truth and blended with the parent by
   fixed integer arithmetic is causal and deterministic.
4. The resulting arithmetic stream reconstructs both the encoded and raw
   streams exactly.
5. A positive result requires exact payload replay plus source, state, runtime,
   and transfer accounting; semantic plausibility alone has no value.

State a complete induction invariant and explain why classification of a
partial heading before its terminating boundary would violate causality.
