# Pre-registration: the potential certificate on two real C corpora

Committed on 2026-11-22 (UTC), before any linear program was solved on these corpora. Only their sizes were
measured: programs, bytes, alphabet, and the number of eligible occurrences.

## Corpora

`C-1` and `C-2` from `capacity-diagnostic-v1/independent-eval/independent-instances.json`
(sha256 `941688ab7511851178f62b63fd655f971986a4a0a2d9af7f2e9e3458d963c0b2`), frozen there at Gamma `3e15a8dce`. They were chosen by an isolated selector, not by
this folder's author. Witness rule, threshold 2.

| Corpus | Programs | Bytes | Alphabet | Eligible occurrences | Lower bound in `capacity-diagnostic-v1` | Budgets it leaves unresolved |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| C-1 | 4 | 3,714 | 64 | 40,181 | 61 | 61 to 63 |
| C-2 | 4 | 7,638 | 67 | 70,602 | 65 | 65 to 66 |

The other seven corpora of that evaluation are already settled at every budget and are not run.

## Question

Does the certificate settle the unresolved budgets? There are three possible outcomes per corpus.

| Outcome | Meaning |
| --- | --- |
| The certificate, rounded up, equals the alphabet size | One entry per character is the minimum. Every unresolved budget is `IMPOSSIBLE`. |
| A dictionary smaller than the alphabet is found and its size equals the rounded certificate | The minimum is that size. Every budget is settled. |
| Neither | The unresolved band is narrowed and reported as an interval. |

## Predictions

- **P1.** On C-1 the rounded certificate is at least 62, above the stored lower bound of 61.
- **P2.** On C-2 the rounded certificate is at least 66, above the stored lower bound of 65.
- **P3.** At least one of the two corpora is fully settled by the first or second outcome.

I do not predict which of the first two outcomes occurs. C headers repeat include and guard lines, so a
shared multi-character entry could replace two characters that occur nowhere else. That would put the
minimum below the alphabet size.

## Proved claims

- A stored certificate is valid and its value does not exceed the size of any stored dictionary.
- A stored dictionary has only eligible entries and spells every program byte for byte.

## How it will be checked

`evaluate_real.py` reads `certificates-real.json`, checks each certificate in exact fractions and replays
each dictionary. It uses no solver. `find_real.py` needs scipy and is not trusted. It finds the certificate
with a linear program and searches for a dictionary with an integer program under a 300-second limit per
corpus. Whatever dictionary it returns is replayed; its claim of optimality is recorded and not used.
