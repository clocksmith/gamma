# Isolate the implicit dictionary input

The auxiliary-package parent decoded the opening250KB exactly in its native
source directory, but crashed139 after embedding and extraction in a restricted
filesystem. Source `fxcmv1.cpp` calls `dosym()` from its constructor; this reads
`.dict` implicitly and activates a legacy reverse-dictionary model. The successful
native directory has no `.dict`. The extracted directory does.

Freeze three decodes using the identical retained archive9, payload, model,
dictionary and ELF providers: absent-A, present, absent-B. All use the same
explicit `dictionary.bin` argument. Only present additionally exposes the exact
same dictionary as `.dict`. Every arm uses a fresh sandbox and CPU2 guard. No
source, parameters or scientific population change. No host directory is exposed.
Both absent arms must independently reproduce the canonical opening250KB; the
present arm records success or the observed139 exit. Other failures invalidate
this diagnosis. Byte equality across absent repeats is required.

If only presence changes correctness, this demonstrates an undeclared input
boundary and authorizes a correction-only successor that makes the static-profile
predictor independent of ambient dictionary lookup. It does not authorize merely
renaming extracted files in a submitted package. Preserve the failed parent and
its assets. No gain, full-corpus score or general package closure is claimed.
