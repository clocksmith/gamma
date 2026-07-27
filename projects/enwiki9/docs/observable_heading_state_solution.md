# QH-1 Solution: Observable Heading-State Prediction

Maintain the invariant that, before each encoded bit, encoder and decoder have:

1. decoded the same encoded prefix;
2. released the same complete raw expansions;
3. accumulated the same unfinished raw line;
4. entered the same heading state;
5. stored identical predictor counts.

It holds initially. Given the invariant, both sides compute the same context,
auxiliary probability, and integer blend before truth. Arithmetic decoding
recovers the encoder's bit, after which both update the same count.

If the bit does not complete an emission group, raw line and heading state do
not change. When a group completes, both sides release the same raw bytes and
feed them to the same line automaton. A heading transition is applied only
after its terminating newline is present, so the classification is a function
of completed history. Page boundaries are handled identically. The invariant
therefore propagates.

Induction yields identical encoded bits and raw output. Using characters from
an unfinished heading would expose raw bytes not yet determined by the encoded
prefix and would break the premise that encoder and decoder share the context.

The proof establishes losslessness and causality, not compression. The
classifier and predictor must still improve exact arithmetic bytes after every
counted cost and must transfer to disjoint corpus regions.
