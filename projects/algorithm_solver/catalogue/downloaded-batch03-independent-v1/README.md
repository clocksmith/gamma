# Downloaded third batch: independent qualification (88 pairs)

This directory defines the independent qualification contract for the 88 supplied
JavaScript and Python program pairs imported under
`projects/algorithm_solver/catalogue/authored/downloaded-general88-v1/`.

## Scope and Invariants

- **Inventory:** 88 unique LeetCode problems (IDs 11 through 400), comprising 176
  candidate programs (88 Python, 88 JavaScript).
- **Preservation:** Original delivered sources under `authored/downloaded-general88-v1/`
  remain unmodified and byte-pinned.
- **Authority:** Historical protected Gamma test suites and reserved payloads remain
  closed. No catalogue admission, retrieval slots, or shared qualification machinery
  are modified.
- **Entrypoints:** Qualification evaluates the functional `solve` entrypoints. The
  provided LeetCode `Solution` wrappers are reviewed for syntactic integrity but are
  not execution-qualified here.

## Interface and Functional Adapters

Ten of the 88 problems in official LeetCode specifications require in-place mutation
or return `void`/length `k`:
- **Problems 26, 27, 80:** Official API modifies `nums` in-place and returns integer length `k`.
- **Problems 31, 48, 73, 75, 88, 130, 186:** Official API modifies the array/matrix/board in-place and returns `void`.

The supplied candidate programs implement **functional return-value adapters**:
- They leave input arguments completely unchanged (`args_before == args_after`).
- They construct and return new containers representing the transformed output.
- The wrapper `Solution` methods forward to `solve` and return values rather than mutating in-place.
- In-place mutation contracts are therefore distinguished: functional adapters are qualified under local functional effect contracts; official in-place APIs are explicitly not execution-qualified.

## Permitted Output Freedom and Verification Predicates

- **Multisets and Order-Invariant Sets:** Problems 15, 22, 39, 40, 46, 77, 78, 90, 93, 131, 187, 216, 241, 310, and 347 permit results in any order. The validator sorts canonical element representations before comparison.
- **Group Anagrams (49):** Outer groups and inner word lists may appear in any order.
- **Floating Point (50):** Pow(x, n) is evaluated within numerical tolerance (`math.isclose`, rel_tol=1e-5, abs_tol=1e-7).
- **Disjoint Intervals (56, 57):** Non-overlapping intervals are canonicalized by start coordinate.
- **Gray Code (89):** Sequence validity predicate enforces $2^n$ distinct integers in $[0, 2^n - 1]$ starting at 0 with 1-bit adjacent transitions and 1-bit cyclic closure.
- **Course Schedule II (210):** Valid topological sorting predicate verifies all prerequisites precede dependent courses.
- **K Smallest Pairs (373):** Multiset pair-sum equality validates that candidate pairs match minimal sums.

## Mandatory Algorithm and Memory Requirements

Analysis of official problem statements reveals mandatory complexity gates:
- **Problem 41 (First Missing Positive):** "You must implement an algorithm that runs in O(n) time and uses O(1) auxiliary space." Both Python and JavaScript candidates allocate a hash set of the entire input ($O(n)$ space), failing the mandatory constant-auxiliary-space contract.
- **Problem 164 (Maximum Gap):** "You must write an algorithm that runs in linear time and uses linear extra space." Both candidates use comparison sort ($O(n \log n)$ time), failing the mandatory linear-time requirement.
- **Problem 373 (Find K Pairs with Smallest Sums):** Both candidates materialize all $|nums1| \times |nums2|$ pairs into memory and sort them, violating subquadratic memory and time bounds for inputs up to $10^5$.

These failures are formally registered in `oracles.MANDATORY_FAILURES`.

## Isolated Execution Contract and Host Platform Status

- Gamma evidence contracts require untrusted execution to take place strictly inside
  an authorized isolated judge (`/usr/bin/bwrap`) with private namespaces, disabled
  networking, restricted filesystem mounts, and enforced limits:
  - CPU: 3 seconds
  - Wall clock: 8 seconds
  - Memory: 1 GiB
  - Max output: 16 MiB
  - Repeated first-call per batch for state carryover detection.
- **Host Platform:** macOS Darwin arm64. Linux bubblewrap (`/usr/bin/bwrap`) is absent (`SandboxUnavailable`).
- **Delivery Mode:** In strict adherence to the charter ("If execution is unavailable, deliver the prepared cases and contracts as unexecuted"), all 1,512 generated cases, statement pins, artifact hashes, and batch execution plans are frozen and delivered as unexecuted.
