# Fixed-source vocabulary comparison v1: results

Frozen design: [FREEZE.md](FREEZE.md), committed before any dictionary was built. Source text, dictionaries and certificates stay private; this folder holds hashes, code and source-free aggregates.

| Prediction | Outcome | Measured |
|---|---|---|
| P1: greedy at least 5% below the best baseline at K=256, L=16, both | held | 12.4% fewer tokens (118,336 against 135,034) |
| P2: shortest-path parsing lowers BPE by at least 3% at that cell | **failed** | 0.61% |
| P3: shared beats separate at every K up to 1024, L=16, uncapped | held | shared wins at every feasible budget |
| P4: separate beats shared at K=4096, L=16 | **failed** | shared 42,240, separate 45,666 |
| P5: no-singleton cannot spell all 800 at any K, L=16, proved by reachability | held | 764 of 800 spellable |
| P6: no dictionary below the alphabet spells a whole corpus, by block rank | held | block rank equals the alphabet (91, 92, 94) |
| P7: entries crossing a lexical boundary save more than half at K=256, L=16, both | held | 74% |

## Best verified total tokens against certified lower bounds, entries of at most 16 bytes

| Corpus | Entries | Best BPE | Best found | Lower bound | Gap |
|---|---:|---:|---:|---:|---:|
| python | 128 | 99,924 | 87,239 | 77,141 | 11.6% |
| python | 256 | 66,639 | 57,737 | 51,825 | 10.2% |
| python | 512 | 49,301 | 41,667 | 38,175 | 8.4% |
| python | 1024 | 38,120 | 32,027 | 29,723 | 7.2% |
| python | 2048 | 29,670 | 25,526 | 23,582 | 7.6% |
| python | 4096 | 23,926 | 21,034 | 19,461 | 7.5% |
| javascript | 128 | 81,991 | 67,986 | 60,755 | 10.6% |
| javascript | 256 | 53,712 | 44,699 | 40,300 | 9.8% |
| javascript | 512 | 39,990 | 32,859 | 29,915 | 9.0% |
| javascript | 1024 | 30,846 | 25,220 | 23,058 | 8.6% |
| javascript | 2048 | 23,555 | 19,876 | 18,228 | 8.3% |
| javascript | 4096 | 18,787 | 16,358 | 15,001 | 8.3% |
| both | 128 | 194,048 | 174,584 | 156,732 | 10.2% |
| both | 256 | 135,034 | 118,065 | 105,143 | 10.9% |
| both | 512 | 100,925 | 85,929 | 77,896 | 9.3% |
| both | 1024 | 78,277 | 66,443 | 60,261 | 9.3% |
| both | 2048 | 61,583 | 52,244 | 47,896 | 8.3% |
| both | 4096 | 48,915 | 41,945 | 38,493 | 8.2% |

No cell is a proved optimum. Best found is a verified construction; the lower bound is a certificate rechecked in exact integers.

## Checks

- `verify.py`: 147 chains and 108 polished dictionaries, 13,528 grid cells, every counted file decoded and compared with its frozen hash.
- `verify_sharing.py`: all 384 shared-against-separate splits decoded; the shared dictionary wins all 384.
- `check_bound.py`: 18 dual certificates rechecked in exact integers.
- `check_limits.py`: block rank in two prime fields and no-singleton reachability.
- `test_small.py`: 60 tiny corpora against brute force; tampered certificates refused.

## Scope

In-sample by design: one corpus chooses and evaluates every dictionary. Nothing here measures unseen programs, solving, or model performance. Greedy is a heuristic. Bounds exist only for entries of at most 16 bytes without a byte cap.

## Files

- `results/bounds.json` sha256 `d82886a08fb91688b7de42f9079090fddf951fd9f3c5f754fdb6bd4fd73be548`
- `results/chains.json` sha256 `7243baef18f08690b5646ecb347bcfbb451b48d08d2aaffe644648a0db0571b5`
- `results/limits.json` sha256 `5a5aeeb97bace6d90c781dc17185228d4a27b8ec8526db429dd4622535c3d580`
- `results/sharing-check.json` sha256 `cb19ef209b67dcfd9b5fc67cf24e6042dab7aba3c624771f8fe54b65e8a9827a`
- `results/summary.json` sha256 `7a3598ba4bf1de5869ea9d12dd6eba13757789c54b2478e5cc63b745c565bfd3`
