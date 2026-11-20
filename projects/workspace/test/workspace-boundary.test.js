import { execFileSync } from 'node:child_process';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';
import test from 'node:test';

test('production import guard refuses external workspace modules', () => {
  const dir = mkdtempSync(join(tmpdir(), 'gamma-workspace-boundary-'));
  try {
    const outside = join(dir, 'research.mjs');
    writeFileSync(outside, 'export default {}');
    const hook = fileURLToPath(new URL('./workspace-boundary.js', import.meta.url));
    assert.throws(() => execFileSync(process.execPath,
      ['--import', hook, '--input-type=module', '-e', `await import(${JSON.stringify(pathToFileURL(outside).href)})`],
      { stdio: 'pipe' }), /Workspace import escapes production package/);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});
