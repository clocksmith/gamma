# Reviewed public-batch adoption mechanism v1

`public_batch_adapter.py` is a prospective bridge over the existing canonical
catalogue and independent judge receipts. It is not a second qualification owner.
No batch has been promoted by adding this module.

The trusted operator supplies a SHA256-pinned plan binding the full universe,
predecessor catalogue/receipts, boundary gate, exact freeze, completed report,
run contract, independent verification, execution review and separate statement
identity/domain/interface/effects/complexity authority review. The authority
review must bind every frozen numeric ID and its evidence hashes. A source's
`official=true`, availability or a developer-test report cannot substitute for it.

Only three named sibling verifier lanes are supported: eight-v3, easy16-v1 and
hard10-v1. There is no request-controlled module path. Code hashes are checked
before importing the verifier; its actual full raw-observation replay must equal
the externally pinned verification. Sources/statement authority are opened only
after live boundary authorization. Failed outcomes remain failed; only exact
source-specific passed outcomes can replace a canonical slot. Every prior receipt
and unselected slot is preserved, and replacements archive the prior slot hash.

The mechanism returns in-memory successor artifacts, global-ID source locators
and complete binding descriptors. The caller independently reviews and persists
them. It grants neither publication nor candidate execution. The validator API
checks the exact frozen input domain before any future candidate execution.
Finite tests remain finite evidence, not universal correctness or recognition.

Synthetic tests cover strict external pins, authority bindings, forbidden import
paths, pre-import code drift, canonical replacement/receipt preservation and
frozen input predicates. Actual adoption requires independently reviewed native
execution evidence; these tests do not create it.

## Bounded file reads

Adapter metadata/authority, source and synthetic-case reads use anchored directory
file descriptors with O_NOFOLLOW on every path component. Leaf files must be
regular and bounded; O_NONBLOCK prevents FIFO hangs. Source bytes are capped at
1MiB, observations at4MiB and metadata/case files at64MiB. Sources/cases are
validated before invoking the verifier. The fixed verifier's local Path bindings
are narrowed to the same guarded reader for actual rereads, closing replacement
symlink/FIFO races; global pathlib and historical files remain untouched. This
adapter-level I/O restriction changes no frozen expectation or verdict logic.
