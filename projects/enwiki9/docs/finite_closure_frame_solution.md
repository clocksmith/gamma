# FCF-1: Complete Solution

## Decoder and inversion

The decoder checks the four-byte magic, reads the member count, and repeats
exactly that many times. At each record it reads the two fixed-width lengths,
then consumes exactly the declared path and payload bytes. It rejects a
truncated record, duplicate or unsafe path, invalid UTF-8, and any bytes after
the final record.

Induction on the record index proves inversion. Before record `i`, the decoder
cursor equals the encoder position immediately before that record. Fixed-width
lengths recover the two lengths uniquely, and consuming those exact byte
counts recovers `(p_i, x_i)`. The induction reaches the unique frame end.

## Exact length

The header has six bytes. Every record contributes six length bytes, its path,
and its payload. Hence

```text
L(C) = 6 + sum_i (6 + |utf8(p_i)| + |x_i|).
```

## Safe extraction

For every decoded path, reject absolute paths, `..` components, empty paths,
and duplicates. Join the remaining relative components beneath a fixed root,
create only their parent directories, and write exactly the decoded payload.
No accepted component can move to the root's parent, so every output remains
inside the designated root.

## Quotient and codec transfer

FCF preserves the ordered names and payloads. It deliberately omits USTAR
ownership, mode, timestamp, checksums, 512-byte headers, and block padding.
Those fields are outside the stated closure object.

If frame extraction reconstructs the same path-payload closure as a parent
source package, both packages present identical build inputs. Exact executable
and dictionary hashes then prove identical deterministic codec functions.
Archive bytes agree for every input, so complete score difference equals the
counted package-size difference.

Without closure or runtime identity, omitted metadata may be build-relevant
and no score transfer is valid.

## Frozen enwiki9 screen

On the 73-member BPDQ-1 closure, FCF reduces raw framing from 993,280 to
941,417 bytes. Raw-LZMA2 payload falls from 270,395 to 269,306 bytes, saving
1,089 bytes before wrapper accounting. This is not yet a constructive package
win; the complete decoder wrapper must be smaller by at least one byte.


## Counted frozen transfer

The FCF runtime wrapper is 4,303 bytes. Together with the 269,306-byte
payload, the complete package is 273,609 bytes. This is 300 bytes smaller than
BPDQ-1 and 290,537 bytes smaller than B2 package accounting.

The wrapper's own extraction, dictionary restoration, and build path completed
in 33.87 seconds at 337,264 KiB peak RSS. It reproduced the exact 837,176-byte
executable and 411,996-byte dictionary. FCF-1 is therefore a constructive
package proxy, still with zero score credit until its native exact gate passes.
