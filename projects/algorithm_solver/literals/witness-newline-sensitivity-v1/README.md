# Trailing-newline sensitivity of the matched80 rank (`witness-newline-sensitivity-v1`)

Every matched80 source ends in a newline, and all published matched80 numbers are for those stored bytes.
`check_stripped_rank.py` recomputes the rank of the 80 program vectors with and without the trailing newline
(pin `59ff0441`, field 1,000,000,007, base 2):

| Form | Rank, stored bytes | Rank, newline removed |
| --- | ---: | ---: |
| compact | 79 | 78 |
| canonical | 79 | 79 |

The unrestricted minimum of 79 for the compact form is proved by the rank on the stored bytes. Without the
newlines the rank bound falls to 78. Whether 78 entries then suffice was not tested. The canonical form is
unaffected. Run: `python3 -B check_stripped_rank.py /path/to/gamma` (seconds).
