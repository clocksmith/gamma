# Existing GPU route clears the consumed-fit latency gate

The frozen guarded composer returns **8/10 correct**, zero wrong acceptances,
zero infrastructure failures, and **0.296-second p95** on ten consumed original
fit requests. Raw and structural predictions return 4/10; nearest stored fit graph
returns 9/10. Two semantic failures remain, lcd:1101 and lcd:1489. This establishes
development reuse of the existing GPU embedding route, not 2a completion,
generalization, or superiority to retrieval.

| Route | CPU correct /10 | GPU correct /10 | GPU p95 seconds |
|---|---:|---:|---:|
|Raw|3|4|0.173|
|Structural control|3|4|0.172|
|Frozen guard repair|4|8|0.296|
|Nearest fit graph|3|9|0.166|

CPU guard p95 is 4.470 seconds. Four matched useful answers are lcd:1051, 1046, 2144, 
1710; no CPU-correct answer is lost. This CPU arm was freshly measured with two
threads in the [resource-rejected combined attempt](../typed-gpu-reuse-fit-128-v1/README.md),
then preserved by exact capture/contract/setup hashes before this follow-up.
No query was replaced with a cached speed measurement. It is not a claim about
CPU timing in this later process or a causal hardware-only speed ratio. The older
four-thread 7/10 fresh and 8/10 capture records remain intact.

The model weights, tokenizer, original predictor, corpus and codec hashes were
verified. Real GPU matmul passed with torch 2.12.1+rocm7.2, transformers 5.13.1,
Radeon 8060S and no HSA override. CPU encoder remains float32; GPU uses the existing
historically measured float16 recognition path. Predictor remains CPU float32.
GPU encode synchronizes and returns host vectors inside the timer. No new dtype,
model, dependency, download, query cache, training or service modification.

Numerical equivalence is **not** assumed: six of ten full raw code records differ,
and one neighbor ordering changes. Maximum query-vector absolute difference is
0.000288 and cosine similarity is at least0.99999596. All ten GPU vectors,
neighbors, raw codes and logits exactly match the retained GPU captures from the
first attempt; that is a post-score stability inspection, not a second qualified
speed run. Full CPU memory vectors were not retained by the rejected driver, so
no memory-vector parity claim is made. Expected tests never select either route.

All 80 public route decisions were sealed before hash-bound original independent
source tests were loaded. Full warm-route timing charges embedding, transfer,
retrieval, prediction, graph construction and public verification. Four extra
public executions / 0.25-second repair and 2-second total limits remain unchanged.
Cold encoder setup, fit-memory construction, warmup and independent scoring are
separate. Original 1024-token evaluation truncation is explicitly retained only
for this historical-checkpoint comparison; it grants no new training authority.

The GPU-only follow-up completed in 17.491 seconds with two CPU threads. Peak
sampled process-tree RSS 3.805 GB plus GPU peak reservation 2.510 GB is a conservative
6.315 GB total, below the root 6 GiB allocation; the parallel catalog task has 2 GiB.
GPU peak allocated was 2.203 GB, monitored local assets/run disk 1.389 GB. The first
combined-process failure is preserved. Host workloads remained active, so this
is shared-host development timing, not exclusive-host release qualification.

Evidence: [contract](contract.json), [summary](summary.json),
[parity](parity.json), [post-run config integrity](config-integrity.json), [capture repeat inspection](repeat-capture-check.json),
[capture seal](capture-seal.json), [public decision seal](decisions-seal.json),
[setup](setup.json), [runtime](runtime.json), [driver](run_compare.py).
All raw captures/decisions/independent scores are preserved locally under
`runs/typed-gpu-reuse-fit-128-v2`. Defaults are unchanged. Protected 66 targets and
60 families were not opened; no audit requests were rerun.

Encoder config/tokenizer-config hashes were checked after the run against the
previous frozen fresh-fit manifest and match exactly. This supplemental check is
explicitly post-run; weights/tokenizer payloads were verified before inference.
