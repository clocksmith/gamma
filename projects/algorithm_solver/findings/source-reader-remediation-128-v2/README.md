# Reviewed source readers on 128

The shared campaign verifier now selects the exact approved identity before JSON decoding. Future preparation/replay uses the reviewed scoped helpers; test loading verifies the exact claimed path and raw hash before decoding. Duplicate selected fields fail closed.

The [activation](activation.json) records the new reader identity and reviewed bytes. Independent review passed 42 scoped author checks plus eight independent canaries and 16 shared-reader checks. This is a software boundary check, not solver qualification.

Historical scripts and the earlier shared verifier parsed unrelated source, statement and embedded public-example records. That host-side access violated the pre-decode boundary. The [bounded flow audit](model-context-audit.json) found no direct unselected-payload output, candidate-input or unrelated hidden-file path in the 17 scripts, but does not certify every historical command or actual model-context non-exposure. Historical results and protected identities remain unchanged; no protected scoring is authorized.

Development intake resumed at ledger revision 426 only under the newly recorded reader identity. Concrete future adapters must bind these reviewed helpers and frozen claimed source/test pins. Raw bytes are streamed to select identity prefixes; zero operating-system byte access is not claimed.
