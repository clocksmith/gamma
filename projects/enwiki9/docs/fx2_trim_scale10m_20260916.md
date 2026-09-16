# Frozen native trimming at 10MB

The validated 1MB comparison preserved the exact 131,238-byte native archive
while removing 5,348 source ZIP bytes or 45,056 executable bytes. These are
alternative component prices, not a full submission score or predictive gain.

`fx2_trim_scale10m_v1` takes the testing branch: retain the exact original and
trimmed source ZIPs and test canonical raw interval `[0,10000000)`, initialized
cold. This prefix has historical exposure; no parameters or source changes are
selected on it. The complete canonical corpus was freshly hashed, and the
10,000,000-byte fixture matches its prefix byte for byte.

Both arms rebuild from the frozen ZIP, repeat a clean build, preprocess, encode,
independently decode, and reencode the reconstructed raw input. The fourteen
phases must preserve binary identities, cross-arm preprocessing and archives,
and within-arm repeats. There is no retained 10MB archive being substituted for
fresh measurement. The 1MB reference is not reused at this scale.

Require archive equality and the same component reductions. A reconstruction,
repeat, build or resource failure leaves confirmation incomplete; it is not
evidence of an archive regression. Native probability and optimizer states are
not dumped, so this is a finite archive/inverse test, not universal equivalence.

Use CPU 2 from controller creation, 9,999,998,976 bytes of cgroup memory, no swap,
16,000,000,000 logical scratch bytes and a 24,000-second aggregate stop. Codec
phases each stop at 3,600 seconds, builds at 360, and preprocessing at 180. The
prior 1MB job measured 6,033,920,000 peak cgroup bytes and 14,711,393,154 peak
logical scratch bytes. These are planning measurements, not a resource proof
for the larger input. Delete sparse PPM scratch only after its owner exits.

The model, dictionary and source remain paid dependencies. Complete packaging,
runtime, notices, options and official multiplicities remain unresolved. The
90,000,000-byte objective and unknown full-corpus score are unchanged. This
gate establishes a larger exact native comparator for future predictor changes;
it does not turn code trimming into the missing payload reduction. Do not add
source and executable reductions, inherit another codec's forecast, or launch
full1G automatically. Close this gate and review its evidence before selecting
any next scale or joint mutation.
