# JANUS Paid Residual MDL Plan

Status: predeclared bounded oracle

Score credit: zero

## Distinction from CHIRON

CHIRON trained chronologically and required development and holdout transfer. It
failed that question and remains terminal.

JANUS asks a different legal two-part coding question:

> If future-informed model parameters are explicitly transmitted and counted,
> can a compact frozen causal model describe the fixed corpus cheaply enough to
> close the target debt?

The runtime predictor remains causal. Only offline parameter construction sees
the complete evaluated population. The parameter bytes pay for that
information.

## Fixed Q0 construction

Use the receipt-bound opening-1M endpoint428 probability trace and the same
declared causal model shape used by CHIRON:

```text
WRT reset block            256 bytes
input                      BOS or previous completed WRT byte
embedding width             64
GRU hidden width            96
GRU layers                   2
binary-prefix outputs       255
training epochs              8
parameter quantization      signed int8 per tensor
```

All complete blocks are training and evaluation data. Use the final eighth
epoch; there is no epoch or architecture selection.

## Controls

```text
J0  exact endpoint428 p1
J1  one future-trained scalar residual per binary-prefix node
J2  future-trained quantized JANUS residual
JS  J2 residuals circularly shifted by 4093 WRT bytes
```

The complete parent trace must replay exactly before any training.

## Accounting

The provisional fixed cost is:

```text
compressed int8 tensor certificate
+ compressed JANUS oracle source
```

Report both:

```text
literal 1M two-part result
projected 1G amortized result
```

Only the second is the intended discovery screen. Neither receives score credit.

## Authorization

Authorize a larger paid-model trace only when:

```text
J2 gross gain                  >= 3,000 B/M
J2 projected net gain          >= 2,100 B/M
J2 exact gain                  > J1 exact gain
J2 exact gain                  > JS exact gain
parent trace replay            exact
```

If any gate fails, reject paid frozen recurrent residual modeling unchanged. Do
not sweep model shape, epochs, precision, reset length, optimizer, or
quantization.

A pass authorizes a 10M paid-MDL screen, not a native decoder or forecast
movement.
