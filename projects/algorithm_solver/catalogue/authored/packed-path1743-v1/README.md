# Linked JS1743 memory repair

This new variant replaces per-node neighbor arrays with one packed numeric Map.
The owner-provided source in `leetcode-medium-32-v1` is unchanged. This is a
prospective repair after its pinned64MiB Node run exhausted the heap, not an
assertion that the original algorithm was semantically incorrect.

For a degree-one path vertex, store its signed neighbor as unsigned32 bits. For
a degree-two vertex, store2^32 plus the unsigned XOR of both neighbors. Every
stored value is below2^33 and exactly representable by JavaScript Number. At an
endpoint `packed | 0` recovers the signed neighbor. At an interior node, remove
the marker and XOR the previous signed vertex to recover the other neighbor.
The graph is a simple path with distinct integer vertices in[-100000,100000];
zero is a valid neighbor, never the absent-entry sentinel. Endpoint order,
negative values, mixed edge orientations and extreme values are preserved.

All allocation and mutation is local. The output is a fresh ordinary Array and
all caller input rows remain unchanged. O(n) expected time and O(n) space remain;
a lower measured memory claim awaits the unchanged isolated runtime replay.
No canonical claim ledger is changed, and no source is represented as a byte-for-
byte implementation from the owner's original commit.
