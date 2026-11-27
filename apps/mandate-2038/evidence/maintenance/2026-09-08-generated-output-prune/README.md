# Legacy generated-output prune — September 8, 2026

Removed 201 loose files from obsolete local staging destinations:

- `dist/firebase-public/`: 48 files, executable 0.14.17.
- `dist/internal-review/`: 77 files, executable 0.14.17.
- `dist/firebase/` outside `public/`: 76 files, executable 0.14.16.

The 0.14.17 manifests identify dirty source trees. Preserve their exact historical
bytes, including all three original site manifests, in `legacy-staging.tar.gz`.
This is historical build custody, not current playable content or new qualification.
The archive retains original project-relative member paths. For inspection,
extract into a temporary directory rather than restoring obsolete staging paths.

Archive SHA-256: `09b2cce111d58347ba7550dc94d705b174c3d4de4686ab8a1d2b5de239ff7aa1`.
Each archived member was read back and verified against its original SHA-256
before its loose copy was removed. Every remaining file under `dist/` was then
verified byte-for-byte unchanged. The current public package retains 46 files.
Generated files under `dist/` fell from 658 to 457.

No authored sources, immutable releases, frozen physical kits, deployment checks,
or authoring-verification records were removed. No deployment was performed.
