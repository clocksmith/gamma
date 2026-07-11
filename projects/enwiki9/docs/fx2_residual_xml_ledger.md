# FX2 Residual/XML Ledger

This ledger is the target-substrate screen for compact Wiki/XML residual
mechanisms. It reads the exact cached FX2 probability trace and does not launch
the native compressor.

## Target Contract

The calibrated target gate for a component with `12,000` added program bytes
is:

```text
required_10M_gain
  = (110,181,114 - 109,500,000 + 12,000) / 66.95533418670768
  = 10,351.886200 bytes
```

The trace is split chronologically:

```text
0..199,999 bytes       warmup
200,000..399,999       selection
400,000..600,741       untouched confirmation
```

Models use current FX2 `p1`, bit position, and decoder-visible causal state.
Residual counters and hypothetical regret update only after the current bit.
A context abstains until it has minimum support and positive prior correction
regret. Selection ranks families; confirmation is not used for ranking.

## Exact Result

Receipt:
`results/fx2_residual_xml_ledger/apm1m_causal_xml_v1.json`

- Receipt SHA-256: `c528b9542621ebe3fd064c13a9d3ff784c9fffa9040b5d244763aae860587201`
- FX2 rows: `4,805,936`
- State models ranked: `30`, plus two calibration controls
- State winners exact-replayed: `3`
- Promotion candidates: `0`
- Verdict: `no_state_family_clears_counted_target_gate`

Top selection-ranked state:

| State | Blend | Selection gain over calibration | Confirmation gain over calibration | Exact gross selection | Exact gross confirmation | Confirmation regressions |
|---|---:|---:|---:|---:|---:|---:|
| `tag` | `25,000 ppm` | `0.129394` bytes | `0.084961` bytes | `0` bytes | `0` bytes | `0` |
| `lexer_char` | `50,000 ppm` | `0.127930` bytes | `-0.274902` bytes | `1` byte | `1` byte | `0` |
| `xml_compact` | `50,000 ppm` | `0.127930` bytes | `-0.274902` bytes | `1` byte | `1` byte | `0` |

The `lexer_char` and `xml_compact` gross exact byte is not state gain: the
matching calibration control also saved one exact confirmation byte. No tested
state family approaches the `10,351.886200`-byte calibrated `10M` requirement,
so none earns native compilation or a `10M` compressor gate.

## Trace Observability

The current cache can evaluate lexer/tag, character class, template depth,
numeric class, word length, and coarse layout buckets. It cannot evaluate the
full requested Wiki/XML family:

| Requested state | Observable in current exact trace |
|---|---|
| tag | yes |
| template depth | yes |
| section | no |
| ref | no; always zero |
| URL | no; always zero |
| table | no |
| list | no |
| title echo | no; title/word hashes do not vary |
| page kind | no; always zero |
| template argument | no; always zero |

This is an instrumentation boundary, not negative evidence about the
unobservable algorithms. FX2 predicts the WRT-preprocessed stream, where tag
names and words are tokenized. The next residual mechanism must reconstruct
those semantic states causally from the WRT stream and counted dictionary, then
emit them at the final probability boundary. Re-running more blends over the
current constant coordinates cannot test the intended hypothesis.

## Promotion Rule

Do not compile a native candidate from this receipt. A replacement state trace
or mechanism must:

1. expose WRT-reconstructible section/ref/URL/table/list/title-echo state;
2. retain the calibration control and chronological selection/confirmation
   split;
3. clear `required_10M_gain` after counted program bytes;
4. show bounded or zero confirmation-block regressions;
5. only then earn a native canonical `10M` archive gate.

## WRT-Aware Follow-up

`docs/wrt_wiki_shell_v1.md` records the completed instrumentation follow-up.
The observer is archive-identical and now exposes page/title/prose/ref/URL/
list/template/number/section state plus decoder-built memory hashes. The first
combined SSE and shallow retrieval experts remain non-promotable, so the next
candidate is a page-scoped WRT token trie/copy model rather than another sweep
over either the legacy trace or the negative hash buckets.
