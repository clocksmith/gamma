# Exact flat-string format

A dictionary is `LTD1`, a big-endian uint32 entry count, then a big-endian uint32 UTF-8 byte length and exact bytes for each entry. IDs are zero-based in stored order. The dictionary SHA-256 pins identity. No entry is empty or duplicated.

A packet is `LTV1`, one byte bit width, the 32-byte dictionary SHA-256, a big-endian uint32 selection count, then concatenated unsigned fixed-width IDs from most-significant bit to least-significant bit. Final byte padding is zero and is not a selection. Reject unused IDs, a wrong hash, truncated/trailing bytes and nonzero padding. The packet header costs 41 bytes (328 bits).

Decoded source is exactly the UTF-8 bytes concatenated in ID order. There is no extra wrapper, newline, indentation, import, parameter substitution, renaming or runtime helper injection. JSON copies and assembled files are inspectable artifacts, not hidden decoder state. UI playback/finish/control costs are separate from these offline packets and must be reported by the demo integration.
