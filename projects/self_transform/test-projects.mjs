// CPU contract controls only: no study launch, model, network or new receipt.
import { spawnSync } from 'node:child_process';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
const projects = [
  "self_transform_curvature_v1",
  "self_transform_secant_regen_v1",
  "self_transform_subspace_v1",
  "self_transform_v1",
  "self_transform_v2",
  "self_transform_v3",
  "self_transform_v4",
  "self_transform_v5",
  "self_transform_v6",
  "self_transform_v7"
];
const directory = mkdtempSync(join(tmpdir(), 'gamma-self-transform-tests-'));
let failed = false;
try {
  for (const project of projects) {
    const entry = fileURLToPath(new URL(`./${project}/test.mjs`, import.meta.url));
    const result = spawnSync(process.execPath, [entry], {
      cwd: directory, stdio: 'inherit', timeout: 30000,
    });
    if (result.status !== 0) {
      failed = true;
      console.error(`${project}: ${result.error?.message ?? result.signal ?? result.status}`);
    }
  }
} finally { rmSync(directory, { recursive: true, force: true }); }
process.exitCode = failed ? 1 : 0;
