# NNCP v3.3 LibNC concat-RMSNorm multi-update parity

Candidate: `nncp_v33_libnc_concat_rmsnorm_multiupdate_parity_v1`

Status: frozen source-bound multi-update gate; zero score and forecast credit.

## Population

Use the first 32 raw bytes of the canonical one-billion-byte `enwik9` file.
The miniature has a four-symbol training segment, so the population exercises
eight sequential online updates with evolving parameters and memory. It is not
the older synthetic receipt whose nonzero targets were separated by zeros.

## Source receipt

Build the exact recovered `2024-06-05` NNCP source and an observation-only
coefficient-save hook. The native source uses its deterministic configured
seed; the already source-bound initial tensor export supplies the identical
analytic state. Run the native encoder twice. Require byte-identical:

```text
archive
teacher probability trace
final coefficient package
canonical final tensor export
```

The command line advertises `--load_coefs`, but upstream compiles both load
calls out and the disabled generic expression is not type-correct. This gate
therefore does not pass the inert option or patch the model initializer. Decode
the first archive with the same exact seeded source and require restoration of
the 32 input bytes. A decoder-side teacher trace and first differing byte are
recorded even on a miss so reconstruction defects remain separable from the
analytic update result.

## Analytic replay

Replay all eight segments from the initial tensor export using the frozen
concat-optimized final RMSNorm formula:

```text
inverse * (g - mean(g) - output * mean(g * output))
```

No captured adjoint is available or consumed. Require source probability and
final-tensor errors at or below `2e-5`, plus a byte-identical second analytic
model/probability/loss replay.

A pass authorizes only the smallest faithful-profile constructive prefix gate.
It does not assign bytes to the Hutter forecast. A valid miss exits zero and
retires the analytic contract as a multi-update parity solution without
shortening the population or sweeping optimizer and tolerance settings.
