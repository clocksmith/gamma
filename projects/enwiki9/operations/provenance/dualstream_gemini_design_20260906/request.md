# One executable grammar mutation

Act as a competing codec designer. Return one implementable mutation to the
attached, already measured standalone two-stream grammar codec. Return proposed
code or a precise patch plus the required arguments below. You have no tools;
do not claim to have run a benchmark. Model identity or effort notation is not
evidence of correctness or better reasoning.

The exact opening 250,000-byte development population, codec source, tests and
terminal byte breakdown are attached in the request JSON. The raw bytes are
base64-encoded with an explicit SHA256. They are development data only. No
validation or confirmation bytes are supplied. The remaining corpus and all
HORIZON/MIDAS/FX2 artifacts are outside this request.

Parameterized templates and repeated argument bindings ALREADY EXIST here.
They improve the tested recursive representation but all eight configurations
lose to identically framed plain Deflate. Do not propose their first
implementation again. The recorded literal-definition cost suggests a
representation diagnostic, but this accounting does not prove a unique cause.

Choose one mechanism with a small decoder and bounded development cost. Preserve
the measured v1 source and its unchanged plain and recursive baselines. Use a
separately identified successor and explicit format identity if bytes change.
Do not introduce a model, training pipeline, dependency installation, hidden
dictionary, or another architecture. Prefer a narrow adapter over copying the
whole codec. Every selector, dictionary, argument, framing and entropy backend
byte must be counted. Python/zlib distribution costs remain unresolved.

Return:

1. One hypothesis and a precise changed mechanism, including why the existing
   negative result does not already test it.
2. An implementable patch or complete changed functions, including encoder and
   decoder procedures. Keep configuration fixed at max_rule_length=4,
   grammar_budget=16, min_benefit=1, shortlist=4 and 65,536-byte frames initially.
3. A termination argument and exact-byte preservation argument, including
   malformed input rejection and bounded expansion.
4. Worst-case time, live memory and package additions; distinguish measured
   quantities from unmeasured bounds. Never estimate engineering duration.
5. The smallest synthetic test that could falsify your mutation, followed by
   the exact opening-250KB comparison that could reject it economically.
6. Any missing attribution control. State what your proposed comparison can
   and cannot isolate.

Provide a candidate we can reject from executable evidence. Do not promise a
full-corpus score or extrapolate to the 99,000,000 complete-byte objective.
