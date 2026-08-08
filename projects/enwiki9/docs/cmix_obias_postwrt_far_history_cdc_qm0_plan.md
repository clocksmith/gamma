# cmix-obias Post-WRT Far-History CDC QM0

## Question

The public cmix-obias result totals 108,492,825 bytes, 3,492,825 above the
current 105M objective. Its specialized frontend produces a receipt-bound
587,138,826-byte post-PHDA9/WRT/payload_lex stream before arithmetic coding.
Its exact byte-history ring holds only 60,000,000 bytes. Does the modeled
stream contain enough exact repetition beyond that ring to close the debt with
a paid copy representation?

## Frozen universe

The input is `transformed_ready.bin`, size 587,138,826 and SHA-256
`7826ff63dedd526c119dda08e6e044be8fa8f6e89a55f3d6b1f3447cdfc5c1ce`,
already bound by the passing full-corpus construction/inverse receipt.

The scanner inherits the raw far-history implementation unchanged except for
three preregistered constants:

- expected input size: 587,138,826;
- minimum source distance: 60,000,000;
- average-rate numerator: the donor's 107,726,514-byte modeled payload.

It retains the 32-byte window, low-six-bit anchor, two independent 64-bit
hashes, exact comparison before extension, 64-byte minimum match, earliest
source, fully closed source, maximal extension, and chronological nonoverlap.
Each selected command is serialized as columnar canonical ULEB128 literal gap,
distance, and length. Two scans, raw ledgers, and compressed ledgers must agree.

## Gate

Copied bytes are priced at `107,726,514 / 587,138,826`. The actual compressed
ledger and a fixed 65,536-byte integration allowance are subtracted. Promotion
requires at least 40M copied bytes, 4.5M net payload-rate-equivalent bytes, and
positive coverage in every stream third. This exceeds the donor's 3,492,825
score debt plus bounded integration and transfer reserve.

A pass authorizes a separately frozen native donor integration: decode the
cmix residual, reconstruct this exact modeled stream, then run the existing
payload_lex/WRT/PHDA9 inverse. A miss retires this realization without nearby
anchor, source, length, or coder sweeps. The ceiling is external-parent,
average-rate evidence and earns zero score credit.
