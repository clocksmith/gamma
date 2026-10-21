# Reuse a counted counter in minimum-window source

A qualified #76 source rewrite reuses a counting helper from existing development
alternatives for #242 and #594. With unchanged dictionaries, the ranked
100-problem eight-bit control improves from 6,963 to **6,938 selections**,
p95 153 to **148**, and 14,005 to **13,980 package bytes**. Median stays 58.5;
character bits are 53.272%. The heap dictionary instead yields **7,043 selections
and 13,755 bytes**. Keep its storage advantage explicit.

The ranked seven-bit arm improves from 11,558 to 11,549 selections and from
15,750 to 15,742 bytes. This is a matched source-only change, not dictionary
learning or autonomous composition. M1 remains unmet on this 100-program subset.

The rewrite preserves UTF-16 code-unit behavior through a split array and a
concrete object counter. Single-code-unit keys cannot match inherited names such
as `constructor`; the qualification assumes a pristine judge realm. Every helper
byte is encoded. Expected linear time is preserved; the split adds O(m) temporary
storage. No runtime speedup is claimed.

Original and two rewritten syntax choices pass **6,696 checks on 2,232 distinct
cases**, including exhaustive short strings, Unicode/surrogate boundaries and
100,001-character stress inputs. Expected values stay outside the native sandbox.
Exact outputs, argument preservation and alias checks pass. **800 packets**
independently decode and pass forward shortest-path/cost audits.

[Contract](evidence/contract.json) · [Qualification](evidence/qualification.json) ·
[Results](evidence/initial-result.json) · [Packet audit](evidence/packet-audit.json)

The method directory preserves the exact executed verifier, measurement and audit
scripts, including their original private-run paths. These are frozen provenance,
not portable CLI wrappers. Reproduction needs the hash-bound private inputs and
sources, which are not published here. Reconstructed sequences are offline
encoding evidence, not description-to-program synthesis. The
[matrix successor](../matrix-kernels-v1/README.md) uses this result as its baseline.
