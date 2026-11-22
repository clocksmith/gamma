# Pre-registration: Independent Whole-Project JS / Python / C Diagnostic Evaluation

Selected by an isolated read-only subagent (`92b412f0`) that had **zero access** to `capacity-diagnostic-v1/`, `capacity-theorems-v1/`, `capacity-impossibility-v1/`, `witness-coverage-v1/`, `sixbit-v1/`, or anything under `projects/algorithm_solver/`.

Committed **before** running `diagnostic.py` or `evaluate_independent.py` on any corpus in `independent-instances.json`.

## Rules Frozen Before Scoring

- **Eligibility rule:** Witness rule $W_2$ (`k = 2`), whole programs excluded, multi-character UTF-8 cap `160` bytes, singletons in $\Sigma$ eligible whenever not whole programs.
- **Whole-project separation:** Zero overlap with `projects/algorithm_solver/` and zero project or file overlap across the 9 corpora.
  - 7 corpora pinned to `clocksmith/gamma@59ff04415ff2afd04ff2ed451340f4f02852bf18` (`JS-1`, `JS-2`, `JS-3`, `PY-1`, `PY-2`, `PY-3`, `C-3`).
  - 2 compact borderline C corpora pinned to `clocksmith/fawn@a281360ff04321f08e5627c5309503d0259a0e70` (`C-1`, `C-2`).
- **Reporting discipline:**
  - Compare `diagnostic.py` against `alphabet_size` (`|\Sigma|`), `forced_singletons` (`|F_1|`), `mandatory_block_rank` alone, and `disjoint_position` alone on every query.
  - Report the exact fraction settled without a solver (`IMPOSSIBLE` or `FEASIBLE` with byte-exact reconstruction).
  - Do **not** count `UNRESOLVED` as either a wrong answer or a predicted success.
  - Report measured runtime (`elapsedMs`) and peak traced memory (`peakAllocKiB`) for every query.

## The 9 Independent Corpora & 27 Pre-Registered Queries

| ID | Lang | Pinned Repo@SHA | Origin | Files | Bytes | `|\Sigma|` | Budgets `K` | Selector Prediction |
| :--- | :--- | :--- | :--- | ---: | ---: | ---: | :--- | :--- |
| `JS-1` | JS | `gamma@59ff0441` | Mandate 2038 rule tests | 4 | 3,133 | 59 | 48, 64, 72 | 48 IMP; 64 FEAS; 72 FEAS |
| `JS-2` | JS | `gamma@59ff0441` | Gamma web frontend utils + game | 6 | 7,606 | 75 | 64, 76, 96 | 64 IMP; 76 FEAS; 96 FEAS |
| `JS-3` | JS | `gamma@59ff0441` | Reconfiguration rank-one exp. | 7 | 18,645 | 90 | 64, 92, 128 | 64 IMP; 92 FEAS; 128 FEAS |
| `PY-1` | Py | `gamma@59ff0441` | Gamma SWE search/write scripts | 4 | 5,128 | 61 | 52, 64, 72 | 52 IMP; 64 FEAS; 72 FEAS |
| `PY-2` | Py | `gamma@59ff0441` | FunctionGemma training pkg | 5 | 15,208 | 76 | 64, 78, 96 | 64 IMP; 78 FEAS; 96 FEAS |
| `PY-3` | Py | `gamma@59ff0441` | Mind-Meld strategies pkg | 4 | 27,129 | 86 | 64, 88, 128 | 64 IMP; 88 FEAS; 128 FEAS |
| `C-1` | C | `fawn@a281360f` | Doe Metal frontend headers | 4 | 3,714 | 64 | 56, 64, 72 | 56 IMP; 64 FEAS (knife-edge); 72 FEAS |
| `C-2` | C | `fawn@a281360f` | Doe Metal ObjC ABI type headers | 4 | 7,638 | 67 | 64, 68, 80 | 64 UNRES/IMP (borderline); 68 FEAS; 80 FEAS |
| `C-3` | C | `gamma@59ff0441` | Enwiki9 NNCP C hooks | 5 | 13,426 | 85 | 64, 88, 128 | 64 IMP; 88 FEAS; 128 FEAS |
