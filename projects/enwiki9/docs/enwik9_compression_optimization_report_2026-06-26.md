# A Rigorous Systems and Information-Theoretic Report on the `enwik9` Compression Optimization Project

**Date:** June 26, 2026
**Target corpus:** `enwik9`, exactly $10^9$ bytes of English Wikipedia XML/text
**Project phase:** active benchmarking, memory shaping, and determinism validation
**Primary objective:** minimize the Hutter-style ledger score while preserving exact reconstruction under the memory/time envelope

---

## 1. Executive thesis

This project is not primarily a search for a clever textual preprocessor. It is a constrained sequential prediction problem. A lossless compressor wins by assigning high probability to the exact next bit before that bit is known. A systems implementation wins only if the reduction in negative log-likelihood is larger than the additional bytes required to ship the code, tables, dictionaries, transforms, and wrappers that make the prediction possible.

The correct optimization target is therefore not raw transformed size, local compression ratio, or isolated benchmark score at 1 MB. The target is the ledger-adjusted description length

$$
S = A + P,
$$

where $A$ is the final archive/self-extracting payload in bytes and $P$ is the byte cost of all shipped executable logic and runtime resources that are counted by the benchmark/prize rules.

At the bit level, if the compressor predicts bit $y_t \in \{0,1\}$ with causal probability $q_t = P(y_t=1 \mid y_{<t})$, then the ideal arithmetic/range-coding length is

$$
L(q;y_{1:T}) = \sum_{t=1}^{T}
\ell_t(q_t,y_t)
= \sum_{t=1}^{T}
\left[-y_t\log_2 q_t - (1-y_t)\log_2(1-q_t)\right],
$$

up to small coder overhead and file-format overhead. Since `enwik9` has $T=8\cdot10^9$ bits, a score improvement of 1 byte corresponds to 8 bits of codelength. The engineering problem is therefore:

$$
\min_{\theta,\,\text{program}} \quad
\frac{1}{8} L(q_\theta;y_{1:T}) + P(\theta,\text{program})
\quad\text{subject to}\quad
\text{RSS}_{\max}\le M_{\max},\;\text{decode}(\text{archive})=\texttt{enwik9}.
$$

This formulation forces every proposed change to answer three questions:

1. **Does it reduce causal log-loss?**
   Measure $\Delta L$ in bits using an exact shadow coder or paired online log-loss trace.
2. **Does it cost bytes?**
   Include compiled code, static data, dictionaries, sort keys, wrappers, and metadata.
3. **Does it survive resource constraints?**
   Verify peak RSS, deterministic roundtrip, and wall-clock behavior on compression and decompression, not only on compression.

---

## 2. Benchmark ledger and quantitative targets

The public Hutter-style record to beat is currently associated with `fx2-cmix`, with total size

$$
L = 110{,}793{,}128\text{ bytes}.
$$

A formal 1% improvement threshold is

$$
S \le \lfloor 0.99L\rfloor = 109{,}685{,}196\text{ bytes},
$$

or equivalently $S < 109{,}685{,}197$ bytes.

Your project target

$$
S_{\text{target}} = 109{,}500{,}000\text{ bytes}
$$

is stricter than the 1% threshold by

$$
109{,}685{,}196 - 109{,}500{,}000 = 185{,}196\text{ bytes}.
$$

If the calibrated internal baseline is

$$
S_{\text{baseline}} = 110{,}181{,}114\text{ bytes},
$$

then the project needs

$$
\Delta S_{\text{baseline}\to\text{target}}
= 110{,}181{,}114 - 109{,}500{,}000
= 681{,}114\text{ bytes}
= 5{,}448{,}912\text{ bits}.
$$

Normalized to the input size, this is

$$
\Delta\mathrm{bpb}
= \frac{8\cdot681{,}114}{10^9}
= 0.005448912\text{ bits/input byte}.
$$

At a 10 MB screening scale, a naive linear target would be

$$
681{,}114\cdot\frac{10^7}{10^9}=6{,}811.14\text{ bytes}.
$$

That number is useful as a first-order screening heuristic, but it is not a proof. Wikipedia is heterogeneous: article starts, XML metadata, lists, references, infoboxes, math, tables, redirects, and natural prose do not scale identically. Any candidate that passes 10 MB must still be checked on larger prefixes and, ideally, on page-stratified samples.

### Ledger interpretation

A change with archive saving $\Delta A$ and program/resource overhead $\Delta P$ is beneficial only when

$$
\Delta S = \Delta A - \Delta P > 0.
$$

Equivalently, in bits:

$$
\Delta L_{\text{bits}} > 8\Delta P.
$$

This is the Minimum Description Length (MDL) discipline for the project: no helper parser, sort routine, finite-state machine, table, or dictionary should be merged unless its measured causal log-loss reduction exceeds its shipped byte cost by a safety margin.

---

## 3. Compression as sequential probability estimation

A modern high-ratio text compressor can be viewed as two separable components:

1. A **predictor** that computes $q_t=P(y_t=1\mid H_t)$ from the decoded history $H_t=y_{<t}$.
2. A **range/arithmetic coder** that converts those probabilities into bits close to the cross-entropy bound.

The range coder is nearly optimal once the probabilities are fixed. Almost all meaningful improvement must therefore come from better causal probability estimates or from a reversible transform that exposes easier-to-predict structure without costing too many bytes.

For two predictors $A$ and $B$, the exact log-loss delta over a test stream is

$$
\Delta L_{A\to B}
= \sum_t \left[\ell_t(q^A_t,y_t)-\ell_t(q^B_t,y_t)\right].
$$

If $\Delta L_{A\to B}=80{,}000$ bits, the ideal archive saving is about $10{,}000$ bytes before headers and coder rounding. If the implementation adds a 12,000-byte parser, the net ledger change is negative even though the statistical model improved.

This is why the project should report every experiment in four units:

| Quantity | Symbol | Unit | Why it matters |
|---|---:|---:|---|
| Causal log-loss delta | $\Delta L$ | bits | The real statistical gain |
| Archive delta | $\Delta A$ | bytes | What the coder actually saved |
| Program/resource delta | $\Delta P$ | bytes | What the ledger charges |
| Memory delta | $\Delta M$ | KiB | Whether the candidate is admissible |

---

## 4. Algorithmic context, corrected and grounded

### 4.1 Prediction by Partial Matching (PPM)

PPM is a variable-order Markov model over symbols. For a context $c=x_{t-k}^{t-1}$, it stores counts $n_c(a)$ for observed next symbols $a$. If the symbol has been seen in the longest context, it is encoded with a probability derived from the count table. If not, the model emits an escape event and backs off to a shorter context.

A generic PPM backoff distribution can be written as

$$
P(a\mid c)=
\begin{cases}
\widehat P_c(a), & n_c(a)>0,\\[4pt]
P_{\mathrm{esc}}(c)\,P(a\mid \operatorname{suffix}(c)), & n_c(a)=0,
\end{cases}
$$

with exclusion rules preventing symbols already assigned probability in higher contexts from being double counted at lower orders. Different PPM variants are mostly different choices of $\widehat P_c(a)$, $P_{\mathrm{esc}}(c)$, update rules, exclusion rules, and memory management.

The important project-level point is not one specific escape formula. The important point is that PPM trades **context specificity** against **statistical support**. Longer contexts reduce bias when they have enough observations, but increase variance and memory pressure when counts are sparse. That is exactly the same bias-variance problem encountered in context maps, APMs, and expert routers.

### 4.2 LZ-style parsing

LZ77/LZMA-style methods encode repeated substrings as backward references. Their strength is exact repetition. They are theoretically universal under broad stationary assumptions, but on a finite 1 GB heterogeneous XML/prose corpus, exact-match parsing alone cannot exploit every semantic, syntactic, and markup regularity. It also competes with memory constraints: longer dictionaries improve match discovery but increase working-set pressure.

For this project, LZ-like preprocessing should be treated as useful only when it preserves the statistical context expected by the downstream model. Replacing frequent XML fragments with private opcodes may help a simpler backend, but it can harm a context mixer that already has strong byte, word, match, and markup models trained on the natural byte stream.

### 4.3 Burrows-Wheeler transform (BWT)

BWT is a reversible block transform. It sorts cyclic rotations or, equivalently in practical implementations, uses suffix-array-like structure to group symbols that share following contexts. The transformed block often contains runs that are easy to compress with move-to-front, run-length coding, and entropy coding.

The key limitation for this project is not that BWT is mathematically weak. It is that a BWT pipeline and a PAQ/cmix pipeline optimize different objects. BWT is a block transform; cmix-like systems are online bit predictors with dense adaptive state. A BWT transform may destroy byte-level temporal features that existing high-order models use. Therefore, any transform must be judged by downstream log-loss, not by raw transformed file size.

### 4.4 Context mixing and PAQ/cmix-style prediction

A context mixer combines predictions from many weak or specialized models. Let model $i$ output $p_i=P_i(y_t=1\mid H_t)$. The usual logistic mixing form is

$$
x_i = \operatorname{logit}(p_i)=\ln\frac{p_i}{1-p_i},
$$

$$
q_t = \sigma\left(b+\sum_i w_i x_i\right),
\qquad
\sigma(z)=\frac{1}{1+e^{-z}}.
$$

The cross-entropy loss in bits is

$$
\ell_t(q_t,y_t)= -y_t\log_2 q_t-(1-y_t)\log_2(1-q_t).
$$

The gradient is

$$
\frac{\partial \ell_t}{\partial w_i}
= \frac{q_t-y_t}{\ln 2}\,x_i.
$$

Absorbing $1/\ln 2$ into the learning rate gives the standard online update

$$
w_i \leftarrow w_i + \eta (y_t-q_t)x_i.
$$

This formula explains why hard probability forcing is dangerous. If the final emitted probability is clamped to $\epsilon$ or $1-\epsilon$ without making the mixer state and training update consistent, the coder, the model, and the online learner no longer optimize the same loss. A wrong high-confidence clamp is catastrophic:

$$
-\log_2(\epsilon)\quad\text{bits}
$$

for one bit. With $\epsilon=2^{-15}$, one wrong forced bit costs 15 bits, enough to erase many tiny gains.

A safer intervention is to add a bounded, trainable logit feature:

$$
q'_t = \sigma\left(\operatorname{logit}(q_t)+\alpha z_t\right),
\qquad |z_t|\le z_{\max},
$$

where $z_t$ is a causal parser feature and $\alpha$ is learned or MDL-gated. This changes probabilities softly and preserves the training objective.

---

## 5. Lessons from failed interventions

### 5.1 Raw byte-stream rewriting failed because it optimized the wrong backend

The opcode preprocessor reduced apparent repetition, but it changed the distribution that the downstream context mixer had learned to exploit. In a PAQ/cmix-style model, the raw byte stream is not just data; it is the coordinate system for high-order contexts, sparse contexts, word models, match models, and APM keys.

Let $h_t=f(y_{<t})$ be a high-order context hash. A transform $T$ is safe only if the new context process $f(T(y)_{<t})$ preserves or improves the sufficient statistics used by the predictor. An opcode transform can reduce raw length while increasing

$$
\sum_t -\log_2 q_t(T(y)_t\mid T(y)_{<t}),
$$

because existing contexts no longer collide with useful historical states.

### 5.2 Hard hash mutation caused context-space dilution

Suppose a table entry originally receives $n$ updates for a context $c$. If a structural variable $z\in\{1,\ldots,K\}$ is appended to the primary hash, the expected count in state $(c,z)$ becomes approximately $n\pi_z$. If $K$ is large or imbalanced, many cells have low support.

For a Bernoulli estimate, the variance term is roughly

$$
\operatorname{Var}(\widehat p)\approx \frac{p(1-p)}{n}.
$$

After splitting by $z$, the variance becomes

$$
\operatorname{Var}(\widehat p_z)\approx \frac{p_z(1-p_z)}{n\pi_z}.
$$

Unless the conditional distributions $p_z$ differ enough to compensate for the loss of sample size, the split increases redundancy. This is the formal version of context-space dilution.

The correct rule is:

> Do not split high-order base contexts unless the measured reduction in conditional entropy exceeds the variance and memory cost of the split.

Therefore structural state should enter late, softly, and with abstention: as an APM/SSE coordinate, a bounded logit feature, or a small expert-router state--not as a mutation of the primary byte-history hash.

### 5.3 Small 10 MB wins are not automatically scalable

A 33-byte gain at 10 MB is positive, but it is statistically fragile. The paired log-loss delta should be reported by page block or byte block:

$$
d_b = \sum_{t\in b} \left[\ell_t(q^A_t,y_t)-\ell_t(q^B_t,y_t)\right].
$$

Then estimate whether $\mathbb{E}[d_b] > 0$ across heterogeneous blocks. A candidate is credible when gains appear across multiple content classes or when losses are explainable and bounded.

---

## 6. Proposed architecture, expressed as testable algorithms

### Path 1: Memory-lensed `cmix21` allocation

Treat each large table or model family as a memory budget variable $m_i$. The objective is constrained empirical risk minimization:

$$
\min_{m_1,\ldots,m_k} L(m_1,
\ldots,m_k)
\quad\text{subject to}\quad
\sum_i m_i + M_{\text{fixed}} \le M_{\max}.
$$

For each table $i$, estimate the finite-difference memory efficiency

$$
\gamma_i
= \frac{L(m_i-\Delta m_i)-L(m_i)}{\Delta m_i}
\quad
\left[\frac{\text{bits lost}}{\text{KiB saved}}\right].
$$

A lower $\gamma_i$ means memory can be removed more cheaply. The allocator-search rule is:

1. Measure $\gamma_i$ for each candidate table under identical seeds, compiler, input prefix, and logging mode.
2. Cut the table with the smallest stable $\gamma_i$.
3. Re-measure because interactions are nonlinear.
4. Stop when $\text{RSS}_{\max}$ has a safety margin, not merely when the average RSS is below the guard.

The current `ppmd22m` result should be described as a promising observation, not yet proof of a general regularization effect. The claim "smaller PPMD improved compression" is credible only if repeated across enough blocks to rule out run noise or prefix-specific effects.

#### Fast range reduction

For a uniform 32-bit hash $h$, the mapping

```cpp
inline uint32_t fast_range_reduce(uint32_t h, uint32_t n) {
    return (uint32_t)(((uint64_t)h * (uint64_t)n) >> 32);
}
```

computes

$$
\left\lfloor\frac{h n}{2^{32}}\right\rfloor.
$$

It maps into $[0,n)$ without division. If $h$ is close to uniform, each bucket receives either $\lfloor 2^{32}/n\rfloor$ or $\lceil 2^{32}/n\rceil$ hash values, so the bias is negligible for compression tables. The important implementation requirement is that the upstream hash must be well mixed; fast range reduction does not fix a biased hash.

### Path 2: Page-geometry ordering as an invertible transform

Let pages be $p_1,\ldots,p_N$. A page ordering $\pi$ changes the compression objective to

$$
L(\pi)=\sum_{j=1}^{N} -\log_2 Q(p_{\pi_j}\mid p_{\pi_1},\ldots,p_{\pi_{j-1}}).
$$

A perfect optimizer is intractable. The practical approximation is to define a transition cost

$$
c(i,j)=L(p_j\mid\text{history ending in }p_i)-L(p_j\mid\text{reset or average history}),
$$

then search for an ordering that reduces total transition cost. Semantic embeddings, title features, namespaces, redirects, infobox templates, categories, and article length are only heuristics for minimizing this empirical transition loss.

The transform is valid only if it is exactly invertible. There are two clean designs:

1. **Stored permutation:** store enough information to invert the order. This has direct ledger cost.
2. **Deterministic key:** decode pages in transformed order, then reconstruct original order using page IDs, stable XML metadata, or another deterministic key already present in the decoded page content. The sorting logic must be shipped, but the permutation itself need not be.

The MDL test is:

$$
\Delta S_{\text{page-sort}}
= \frac{L_{\text{original order}}-L_{\text{sorted order}}}{8}
- P_{\text{sort logic}}
- P_{\text{metadata}}
>0.
$$

Offline deep embeddings may be used during research to discover a simple deterministic key, but the deployed decompressor cannot depend on an unshipped neural embedding model or a hidden future-derived table. If the discovered rule is "sort by deterministic page features already decoded," it is admissible as an algorithm. If the rule requires a learned table or model, that object belongs in the ledger.

### Path 3: Causal parser state as soft calibration, not stream mutation

Define a parser state

$$
z_t = g(y_{<t})
$$

where $g$ is deterministic and uses only the decoded prefix. Examples include XML tag state, wiki-link depth, template depth, URL state, numeric/table mode, and paragraph/list mode.

A safe calibration layer does not replace the base predictor. It adjusts it:

$$
q'_t = \operatorname{APM}(q_t,z_t,b_t),
$$

where $b_t$ is bit position within the byte or another small causal coordinate. A standard APM table can store calibrated probabilities indexed by a quantized prediction bin and context key:

$$
q'_t=(1-\lambda)T[k,j]+\lambda T[k,j+1],
$$

with an online update toward $y_t$:

$$
T[k,j] \leftarrow T[k,j] + \eta(y_t-T[k,j]).
$$

The parser state should abstain when support is weak. Replace raw confidence ratios with a Bayesian or MDL criterion. For a candidate feature $z$, compute the empirical gain over a validation stream:

$$
G_z = \sum_{t:z_t=z}
\left[\ell_t(q_t,y_t)-\ell_t(q'_t,y_t)\right].
$$

Activate the feature only if

$$
G_z > 8P_z + \tau_z,
$$

where $P_z$ is the byte cost of implementing/storing that feature and $\tau_z$ is a safety margin for statistical uncertainty.

### Expert router with regret control

Instead of hard-selecting one expert, maintain $K$ small experts with probabilities $p_{j,t}$. A mathematically grounded causal mixture is exponential weighting:

$$
w_{j,t} = \frac{\exp(-\eta L_{j,t})}{\sum_{r=1}^{K}\exp(-\eta L_{r,t})},
\qquad
q_t = \sum_{j=1}^{K} w_{j,t}p_{j,t},
$$

where

$$
L_{j,t}=\sum_{\tau=t-W}^{t-1} -\log_2 P_j(y_\tau).
$$

This has two advantages over a hard argmin router:

1. It is fully causal and requires no side information.
2. It avoids abrupt transitions when the best local expert changes.

For implementation, the weights can be quantized or converted into a small SSE/APM context coordinate, but the measured criterion remains the same: net reduction in causal log-loss after counting code size.

---

## 7. Empirical status of the current candidate

The current project log describes the active candidate as:

```bash
cmix21_text_mmap_paq5_ppmd22m_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1
```

Internal reported gates:

| Gate | Reported archive size | Status | Interpretation |
|---:|---:|---|---|
| 1 KB | 247 bytes | passed | smoke test only |
| 250 KB | 45,178 bytes | passed | early sanity check |
| 1 MB | 174,531 bytes | passed | near unconstrained baseline, reported +133 bytes |
| 10 MB | 1,638,101 bytes | compression completed | reported 33 bytes better than `ppmd23m`; needs replay proof and larger scale |

The reported replay RSS sample is

$$
10{,}472{,}900\text{ KiB},
$$

against an internal guard of

$$
10{,}485{,}760\text{ KiB}.
$$

The reported headroom is therefore

$$
10{,}485{,}760 - 10{,}472{,}900 = 12{,}860\text{ KiB}.
$$

This is too narrow for comfort. A production-grade validation should track:

- peak RSS sampled at high frequency;
- `/proc/self/status` high-water mark where available;
- major/minor page faults;
- mmap-backed versus anonymous resident memory;
- compression and decompression separately;
- deterministic roundtrip hash of the restored bytes;
- sensitivity to ASLR, allocator, compiler version, and environment.

A candidate should be called "admissible" only after deterministic decompression finishes and the restored byte stream matches `enwik9` exactly.

---

## 8. Validation protocol

### 8.1 Exact shadow coder

For each candidate, run the baseline and modified predictor on the same stream and log paired deltas:

$$
\delta_t = \ell_t(q^{\text{base}}_t,y_t)-\ell_t(q^{\text{cand}}_t,y_t).
$$

Then aggregate by content block:

$$
D_b = \sum_{t\in b}\delta_t.
$$

Report:

- total $\sum_b D_b$ in bits;
- expected byte saving $\sum_b D_b/8$;
- block-level median and quartiles;
- number of blocks won/lost;
- largest negative block;
- content type of largest losses.

This prevents a single favorable prefix from masquerading as a robust full-corpus improvement.

### 8.2 MDL gate

For each feature branch:

$$
\mathrm{NetBytes}
= \frac{\Delta L_{\text{bits}}}{8}
- \Delta P_{\text{bytes}}.
$$

Merge only if:

$$
\mathrm{NetBytes}>\text{safety margin}.
$$

A reasonable safety margin should scale with feature complexity and validation uncertainty. For tiny code changes, a few hundred bytes may be enough. For parser logic, routing, or tables, require a larger margin and validation at multiple corpus scales.

### 8.3 Memory gate

Use memory as a first-class metric:

$$
\text{SafetyRSS}=M_{\max}-\max_t\text{RSS}(t).
$$

Do not accept a configuration whose only evidence is average RSS. Peak memory kills the run. For the current 12.56 MB reported margin, allocator noise alone can matter. The next systems priority is to reduce transient allocation spikes and make table allocation deterministic.

### 8.4 Scale gate

Use a ladder that detects overfitting:

| Gate | Purpose | Required evidence |
|---:|---|---|
| 1 KB | build/decode sanity | exact roundtrip |
| 250 KB | parser and table smoke test | exact roundtrip, no memory blow-up |
| 1 MB | early log-loss signal | paired log-loss positive or explainable |
| 10 MB | first real heterogeneity test | archive delta plus replay proof |
| 100 MB | scale promotion | block-level wins, stable memory |
| 1 GB | final proof | exact full roundtrip and ledger score |

Do not extrapolate the final score from the 10 MB result without at least one larger promotion gate.

---

## 9. Immediate research plan

### Priority 1: Stabilize memory before adding features

The current reported RSS margin is small. Before adding new parser or router code, reduce memory volatility:

- preallocate all large tables during initialization;
- avoid late allocations during page transitions;
- replace dynamic growth with bounded arenas;
- log every mmap/munmap or allocator region at debug level;
- verify decompression, not just compression.

### Priority 2: Build the allocation-efficiency map

Run controlled ablations for PPMD, FXCM maps, run-context maps, sparse maps, APMs, and match buffers. Record

$$
(\Delta L_i,\Delta A_i,\Delta M_i,\Delta P_i).
$$

Then cut memory by lowest $\gamma_i$ instead of manually stepping parameters.

### Priority 3: Replace hard feature injection with MDL-gated soft calibration

The strongest low-risk path is not another opcode preprocessor. It is a causal parser whose state is visible only to late calibration layers and only when validated.

Recommended first states:

1. XML tag mode: title/text/revision/id/timestamp/comment.
2. Wiki template depth and link depth.
3. URL/external-link mode.
4. Numeric/table/list mode.
5. Sentence/paragraph boundary mode.

Each state must have an abstain path and must be removable if it fails the MDL gate.

### Priority 4: Formalize page-order experiments

For any page-order transform, report:

$$
\Delta S_{\text{sort}}
= \frac{L_{\text{native}}-L_{\text{sorted}}}{8}
- P_{\text{sort/invert}}.
$$

Also prove invertibility with a separate transform roundtrip:

```text
original enwik9 -> parse pages -> transformed page order -> inverse transform -> original enwik9
```

Only then should it be integrated into the compression pipeline.

---

## 10. Claims that should be softened or removed

The original report is directionally strong, but several claims should be downgraded from assertions to hypotheses unless you have full logs:

| Original style of claim | More rigorous replacement |
|---|---|
| "This proves `ppmd22m` regularizes the model." | "On the 10 MB prefix, `ppmd22m` is 33 bytes smaller than `ppmd23m`; block-level and larger-scale tests are needed to determine whether this is true regularization or prefix noise." |
| "Output forcing caused gradient desynchronization." | "Hard clamping changes the probability used by the coder without an equivalent consistent update to model state; wrong high-confidence bits have large log-loss, and observed runs showed net degradation." |
| "SVM-derived sort keys restore optimal page sequence for free." | "A deterministic key can reduce the cost of storing a permutation, but its implementation still has ledger cost and the transform must be exactly invertible." |
| "LLM compressors are inadmissible." | "Large pretrained LLM payloads are generally ledger-prohibitive unless the model/program is small enough or generated from counted code/resources; each neural approach must be evaluated by the same MDL ledger." |
| "BWT cannot adapt bit-by-bit." | "BWT is a block transform rather than an online adaptive bit predictor; it can be excellent in the right pipeline but may not preserve the context structure exploited by cmix-like predictors." |

---

## 11. Final decision rule

A candidate is worth promoting only if all of the following hold:

$$
\frac{\Delta L}{8} - \Delta P > 0,
$$

$$
\text{RSS}_{\max} \le M_{\max}-\text{safety margin},
$$

$$
\operatorname{decode}(\operatorname{encode}(\texttt{enwik9})) = \texttt{enwik9},
$$

and the gain remains positive across larger, more heterogeneous validation scales.

This is the project’s strongest technical framing: every architectural idea is either a measured reduction in sequential cross-entropy under a resource constraint, or it is noise.

---

## 12. References and source anchors

- Cleary, J. G., and Witten, I. H. "Data Compression Using Adaptive Coding and Partial String Matching." IEEE Transactions on Communications, 1984.
- Moffat, A. "Implementing the PPM Data Compression Scheme." IEEE Transactions on Communications, 1990.
- Burrows, M., and Wheeler, D. J. "A Block-Sorting Lossless Data Compression Algorithm." DEC SRC Technical Report 124, 1994.
- Mahoney, M. V. "Adaptive Weighing of Context Models for Lossless Data Compression." Technical Report CS-2005-16, 2005.
- Byron Knoll, `cmix` project documentation and benchmark notes.
- Kaido Orav and Byron Knoll, `fx2-cmix` Hutter Prize submission documentation.
- Hutter Prize / Human Knowledge Compression Contest public rules and FAQ.
- Matt Mahoney, Large Text Compression Benchmark rules and test-data documentation.
