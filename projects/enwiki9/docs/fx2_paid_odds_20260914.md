# Exact paid correction selection on retained native FX2 counts

This development gate prices one fixed probability-correction family against the
unchanged native FX2 parent on exposed raw `[0,250000)`: 151210 modeled WRT bytes
and 1209680 bits. It does not run the native codec or read a confirmation sample.
The supplied external audit motivated exact paid selection; its downloadable
bundle was unavailable locally. Gamma implements and tests this selector
independently and does not claim to have reproduced the external nine tests.

Each pre-truth context is `16 * bit_position + (parent_count >> 12)`, with 128
contexts. Seven fixed odds multipliers are 1, 1/2, 3/4, 7/8, 8/7, 4/3 and 2.
Counts use denominator 65536, nearest rounding with ties upward, and clamping to
1..65535. The parent state is held fixed. A native successor would apply the
correction at the coder boundary and preserve the parent's own cached prediction
and normal learning inputs; that integration has not been demonstrated here.

The complete choice table occupies 48 bytes: three bits per context, including
unused and identity entries. Index 7 is invalid. These bytes are transmitted
information selected using the entire development population. Context lookup is
causal given the table; table fitting is explicitly not an online algorithm.

For each context, maximize the exact product of truth counts. Common Q**n and
the fixed instruction length cancel. The contexts partition events, and choices
do not affect each other or parent predictions, so the independent maxima attain
the global minimum of ideal data plus table cost among 7**128 policies. This is
a restricted-family optimum, not new mathematics or a globally best compressor.
Integer floor/ceiling log-ratio inequalities give exact bounds on ideal savings;
subtract all 384 policy bits. Shared implementation and finite-coder costs are
not included and remain required before archive promotion.

Seven tests cover 5488 exhaustive synthetic joint policies, table inversion and
invalid codewords, count identity, integer gain bounds, charged empty contexts,
causal partitions and trace alignment. The corpus runner rehashes 22 bound inputs,
checks retained P/K encode/repeat coder and archive identity, verifies exact WRT
inversion and all truth bits, and requires independent byte-identical fits.
One CPU, 1GiB memory, 16MiB scratch and a 360-second elapsed stop bound the gate.
Resource or correctness failures cannot be reclassified as compression losses.

This differs from the retired adaptive FX2 residual-ratio calibration, which
saved zero archive bytes on its fixture. It also differs from the recent KDA
oracle: no second model trajectory or free per-bit truth-selected expert is used.
No source ZIP cost from the previous-word confirmation is transferred here.
New g_P, g_S, n_1 and n_2 remain unknown; full-corpus score remains unknown and
objective credit is zero. A positive paid ideal lower bound authorizes pricing a
finite coder and shared implementation only. A nonpositive upper bound rejects
this fixed family's ideal-plus-table economics on this population. Neither
outcome settles other correction families, native feedback changes or 90M.
