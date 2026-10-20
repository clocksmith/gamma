# Source comparison and correction

The identical helper is **167 bytes**, present in all eight changed programs (1,336 bytes in their full uncompressed source). All literal records charge this full length.

All20 complete sources total5,387 bytes, versus4,214 for the prior normalized sources: this pass deliberately adds1,173 raw bytes to expose genuine shared algorithm text. Twelve sources remain byte-identical. Shared text only helps if its vocabulary-slot cost and the costs of every distinct remainder beat selecting whole programs. A167-byte common helper is not eight complete solutions; every solve body must still be represented.

A whole program costs one dictionary entry and covers one problem immediately. A search that rewards completed programs can prefer16 whole entries even when common fragments are promising, because short fragments may add no completed program until several complement fragments are also selected. That explains a plausible search bias, not a verified explanation of a specific trace. No search logs were accessed here, and no impossibility claim follows from the prior16-of20 result.

Useful exact recurring candidates include: the full helper (8 programs), count-map initialization (8), one-argument solve declaration, result initialization/return, and map-entry scan. Test these jointly with residual predicates and the two-argument signatures. Overlapping occurrences cannot be summed as independent savings. No irrelevant helper was added to the remaining12 algorithms.

169 is justified on its strict-majority input promise;961 on its unique-repeated-value promise. In particular961 may select a different value on a multiple-repeat extension. Those domain differences must remain explicit in independent qualification, with any required failing cases preserved.136 instead retains general signed-32-bit XOR semantics through parity counting, at O(k) extra memory.
