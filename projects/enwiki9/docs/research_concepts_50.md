# Compression research concepts

Version 1, supplied by the user on 2026-09-12. This reference combines established
mathematics, engineering principles and proposed design directions. None alone
establishes a winning compressor. The active objective, frozen experiments and
retained results remain authoritative; this document creates no queue, launch
permission, score credit or obligation to implement all fifty ideas.

Use these concepts with the [discovery lenses](../workbench/PROMPTS.md#creative-discovery).
Select a concrete information source or representation, inspect its prior local
results, and name the smallest decisive experiment. Keep mathematical guarantees
within their assumptions and distinguish them from proposed applications here.

## Information and compression economics

1. **Minimum description length:** Minimize the combined cost of data, models, dictionaries, instructions and exceptions; better predictions alone do not suffice. [MDL tutorial][1]
2. **Conditional information gain:** Measure whether proposed context explains errors remaining after existing predictions, rather than identifying repetition already exploited.
3. **Predictive sufficient state:** Search for the smallest retained history preserving useful future predictions, then test whether its maintenance costs pay.
4. **Constructive size certificates:** Turn representations into explicit encoders, decoders and counted lengths; conditional mathematical bounds need corpus witnesses before promotion.
5. **Resource constrained modeling:** Treat precision, architecture and training as choices jointly optimizing compressed data, transmitted parameters, memory and decoding time.
6. **Causal availability:** Every prediction must use information reconstructed or transmitted; encode additional side information whenever an explanation requires future knowledge.
7. **Sequence rather than counts:** Preserve ordering dependencies; identical histograms can describe sequences with different repetition, grammar and predictable continuation behavior.
8. **Package amortization:** Amortize required program and dictionary copies across corpus bytes, while separately charging all recurring framing and reconstruction overhead.
9. **Mechanism complementarity:** Seek experts correcting different residual errors; evaluate combinations jointly because improvements can overlap, cancel or change predictive state.
10. **Scientific identifiability:** Design controls that disrupt the proposed information source, rather than merely renaming contexts while preserving useful predictive relationships.

## Representations, structure and reuse

11. **Recursive grammar induction:** Build phrase programs whose rules reference earlier rules, selecting definitions only when descriptions become smaller after encoding. [SEQUITUR][2]
12. **Parameterized templates:** Represent scaffolding as programs with arguments; reuse arguments across fields while transmitting every exception and original formatting distinction.
13. **Copy edit transducers:** Predict records from earlier records using edit programs, charging donor selection, insertions, deletions, substitutions, lengths and instructions.
14. **Reversible normalization:** Separate canonical forms from residual details, preserving capitalization, whitespace, entities, encoding anomalies and ordering through accounted correction streams.
15. **Pushdown prediction:** Use nesting state to predict tags, delimiters and field transitions; retain escape paths for malformed or unrecognized input.
16. **Semantic virtual time:** Advance histories only when matching roles recur, testing whether separated values become more predictable within alternate timelines.
17. **Relational factorization:** Model dependencies between decoded attributes and later fields, learning shared relationships without assuming neighboring fields determine each other. [Squish][3]
18. **Morphological factorization:** Explore stems, affixes, casing and exceptions as reusable components; compare their representation against byte and word based alternatives.
19. **Joint stream modeling:** Separate structure and content without severing statistical dependencies; let reconstructed structural state condition the next content prediction. [XMLPPM][4]
20. **String attractors:** Study position sets covering repeated substrings, then account for reconstructing references instead of assuming combinatorial repetition saves bytes. [Verification and optimization][5]

## Probability models and adaptive combinations

21. **Context tree weighting:** Combine history depths instead of committing to one, letting evidence balance predictions against shorter, better supported contexts. [Original CTW paper][14]; the user's [Data Compression Explained][6] link is explanatory background.
22. **Context tree switching:** Allow context preferences to evolve as behavior changes, measuring switching redundancy and preserving deterministic decoder synchronized updates. [CTS publication][7]
23. **Hierarchical backoff:** Retain coarse predictions when fine contexts lack evidence; adding a structural key should not discard an effective predictor.
24. **Bayesian expert mixtures:** Combine causal predictions using evidence weights, separately accounting for prior penalties, finite arithmetic, model storage and runtime. [Soft-Bayes][8]
25. **Sleeping specialists:** Activate experts when prerequisites are causally available; define inactive predictions and weight updates to preserve baseline behavior.
26. **Probability calibration:** Improve confidence alongside correctness; test calibration families containing the identity so an accurate predictor need not be distorted by construction. [Beta calibration][9]
27. **Change point modeling:** Infer transitions from decoded evidence, balancing adaptation speed against reset cost and avoiding access to future boundaries.
28. **Bits back coding:** Investigate latent explanations whose costs are partly recoverable, charging initialization, model storage, inference and finite stream termination. [Bit-Swap][10]
29. **Decoder built retrieval:** Construct indexes from reconstructed history, retrieving continuations without transmitted addresses while accounting for collisions, eviction and time.
30. **Predictive state quotienting:** Merge states when future behavior is equivalent or acceptably approximated; quantify lost prediction quality and memory savings.

## Compact learned memory and computation

31. **Learned memory updates:** Treat a learner as recurrent state, adapting from decoded observations rather than accumulating a growing attention cache. [Test-time training][11]
32. **Fast and slow learning:** Separate persistent knowledge from temporary document adaptation, measuring interference, reset effects and decoder synchronized update cost.
33. **Sparse attention:** Spend attention on causal positions, comparing learned retrieval against local windows and charging selection machinery and cache maintenance.
34. **Cache validity:** After parameter updates, determine which activations remain valid; rebuild invalidated state identically instead of mixing incompatible model versions.
35. **Compression aware distillation:** Train smaller predictors to preserve improvements affecting actual code length, rather than matching every hidden activation closely.
36. **Quantization aware objectives:** Optimize storage and coding loss; fewer parameter bits help only when archive penalties remain smaller than savings. [ParetoQ][12]
37. **Exact residual packing:** Compress approximate parameters plus correction bits, reconstructing weights before inference to separate storage savings from prediction changes.
38. **Curvature aware adaptation:** Use sensitivity and curvature to scale updates, testing directions against equally costly random or temporally misaligned corrections. [Online convex optimization][13]
39. **Functional sensitivity:** Measure how parameter changes affect truth probabilities, distinguishing useful predictive directions from gradients reflecting scaling rather than value.
40. **Partial evaluation:** Compile fixed shapes, grammar instructions and tables into specialized code, eliminating machinery without changing reconstructed bytes or probabilities.

## Turning ideas into decisive experiments

41. **Working set locality:** Organize frequently accessed state for memory and cache reuse; reduced allocations can hide expensive paging and refaults.
42. **Exact arithmetic contracts:** Specify rounding, overflow, normalization and update order; verify optimized implementations against an independent reference before trusting gains.
43. **Prediction state invariants:** Prove both sides compute identical probabilities from synchronized states, including clocks, parser state, caches and dictionary updates.
44. **Counterfactual error maps:** Locate expensive prediction failures and test explanations there, distinguishing opportunity from achievable causal gain after coding costs.
45. **Matched component ablations:** Change one component while retaining others, measuring interactions before attributing improvements to semantics, optimization, representation or capacity.
46. **Development selection discipline:** Tune within development budgets, choose candidates on validation data and reserve confirmation for frozen implementations without adjustments.
47. **Cold and warm transfer:** Test samples and matured histories separately; mechanisms requiring distant repetition cannot demonstrate coverage before history exists.
48. **Proof based futility:** Stop when certified remaining opportunity cannot recover cost; distinguish mathematical impossibility from budget exhaustion or incomplete evidence.
49. **Bounded program synthesis:** Search small decoder programs under cost and runtime limits, retaining fallback and validating candidates through exact roundtrips.
50. **Value of information:** Schedule experiments by decision value per resource cost, favoring tests that eliminate uncertainty rather than accumulating infrastructure.

## Applying the context without overstating it

The supplied source links were opened and their bibliographic identities checked
on 2026-09-13 UTC. These are references for the concepts, not certifications of
Gamma implementations. In particular:

- Grammar induction does not by itself prove that a serialized grammar pays.
- Relational-data and XML results do not establish gains on arbitrary Wiki bytes.
- Expert regret guarantees apply to their specified comparators and assumptions;
  they do not provide free experts, finite-codec savings or prize qualification.
- The online convex optimization paper does not establish those guarantees for
  an arbitrary nonconvex recurrent model or a scalar approximation to its updates.
- TTT and ParetoQ motivate design directions; their titles do not prove lossless
  decoder synchronization, runtime compliance or an enwik9 archive improvement.
- A resource stop fails its execution gate. A state or inversion failure invalidates
  the affected compression inference. Neither supplies missing compression results.

## Discovery machinery and reproduction

The user's follow-up distinguishes three claims: a package reproduces exact
bytes; a descendant improves the counted compressor result under matched
conditions; and improved research machinery actually helps produce a better
descendant. The third requires matched search budgets and frozen confirmation,
including evidence that the changed generator, analyzer or selector was used.
An unchanged model proposing another candidate does not establish recursive
improvement. This context creates no additional framework or experiment queue.

Reploid could present proposals and evidence, but native jobs remain behind
`tools/enwiki9_lab.py`. No authenticated Reploid job adapter is established by
the evidence cited here. Peer coordination can support independent experiments
and reproduction; it does not prove distributed adaptive decoding or isolated
timing qualification. Doppler could assist permitted development analysis or
teacher proposals, subject to model and execution authority. Neither tool's
existence establishes useful residual information or compressor improvement.

Any final predictor needs decoder-available information and identical coding
probabilities. Quantization alone is not a synchronization proof. The
[competition rules](https://hutter1.net/prize/hrules.htm), checked 2026-09-13,
charge software and archives according to the submitted arrangement, restrict
external inputs and installations, and prohibit GPU use in the submitted runs.
Development tooling does not make required models or choices free.

Quines motivate explicit reconstruction dependencies, not compulsory replication.
A generator's recipe, seed, runtime and execution costs remain relevant. The
[sign/magnitude package receipt](../operations/provenance/fx2_weight_sign_magnitude_zip_v1_terminal.json)
records a scoped 456-byte package improvement and withholds full-corpus credit.
The [cold 1MB receipt](../operations/provenance/opcode_previous_word_confirmation_v4_terminal_20260912.json)
records g_P=737 and g_S=313, with n_1=627 and n_2=517 as historical source-cost
sensitivities; final packaging is unknown. These retained receipts were read,
not rerun for this context addition. The cold comparator differs from the
strongest counted forecast backend, so its savings do not transfer to that score.

The [suffix alphabet experiment](wrt_suffix_alphabet_20260912.md) tests
concepts 18 and 45 while retaining the strong backend. Its original-dictionary
pretraining control was fixed before execution. Exact archive/inverse/repeat
checks are a bounded black-box screen; internal state witnesses and complete
package qualification remain separate requirements. This context addition does
not alter that frozen experiment or the previously closed cold 1MB comparison.

[1]: https://arxiv.org/abs/math/0406077 "A tutorial introduction to the minimum description length principle"
[2]: https://arxiv.org/abs/cs/9709102 "Identifying Hierarchical Structure in Sequences: A linear-time algorithm"
[3]: https://arxiv.org/abs/1602.04256 "Squish: Near-Optimal Compression for Archival of Relational Datasets"
[4]: https://xmlppm.sourceforge.net/paper/node6.html "Multiplexed hierarchical modeling"
[5]: https://arxiv.org/abs/1803.01695 "String Attractors: Verification and Optimization"
[6]: https://mattmahoney.net/dc/dce.html "Data Compression Explained"
[7]: https://webdocs.cs.ualberta.ca/~bowling/publications/b2hd-12dcc-cts.html "Context Tree Switching"
[8]: https://proceedings.mlr.press/v76/orseau17a.html "Soft-Bayes: Prod for Mixtures of Experts with Log-Loss"
[9]: https://proceedings.mlr.press/v54/kull17a.html "Beta calibration"
[10]: https://proceedings.mlr.press/v97/kingma19a.html "Bit-Swap"
[11]: https://arxiv.org/abs/2407.04620 "Learning to (Learn at Test Time): RNNs with Expressive Hidden States"
[12]: https://arxiv.org/abs/2502.02631 "ParetoQ: Improving Scaling Laws in Extremely Low-bit LLM Quantization"
[13]: https://www.microsoft.com/en-us/research/publication/logarithmic-regret-algorithms-online-convex-optimization/ "Logarithmic Regret Algorithms for Online Convex Optimization"
[14]: https://pure.tue.nl/ws/portalfiles/portal/1383848/Metis122608.pdf "The Context-Tree Weighting Method: Basic Properties"

The suffix screen has now closed its archive checks across two executions:
g_P=-1165 and g_S=277 on the exposed opening250k. Its original filesystem failure
remains separate from the successful control-completion resource gate. This is
an observed loss for the fixed alphabet, not a rejection of morphological
factorization or the other concepts. See the [completed evidence](../operations/provenance/wrt_suffix_alphabet_completed_evidence_20260912.json).
