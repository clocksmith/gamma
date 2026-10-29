import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const root = path.resolve(import.meta.dirname, '../..');
const tool = path.join(root, 'tools/export-v11-grpo-adapter.js');

const help = spawnSync(process.execPath, [tool, '--help'], {
  cwd: root,
  encoding: 'utf8',
});
assert.equal(help.status, 0, help.stderr);
assert.match(help.stdout, /exact checked-in V11 seed-11 GRPO PEFT adapter/);

const tempDir = mkdtempSync(path.join(os.tmpdir(), 'doppler-v11-adapter-export-'));
try {
  const adapterDir = path.join(tempDir, 'adapter');
  const outputDir = path.join(tempDir, 'output');
  mkdirSync(adapterDir, { recursive: true });
  writeFileSync(path.join(adapterDir, 'adapter_model.safetensors'), 'not-the-pinned-adapter');

  const result = spawnSync(process.execPath, [
    tool,
    '--adapter-dir', adapterDir,
    '--output-dir', outputDir,
  ], {
    cwd: root,
    encoding: 'utf8',
  });
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /V11 GRPO adapter SHA-256 mismatch/);
  const receipt = JSON.parse(readFileSync(
    path.join(outputDir, 'doppler-wgsl-qwen35-9b-v11-grpo-seed11.export.receipt.json'),
    'utf8'
  ));
  assert.equal(receipt.ok, false);
  assert.match(receipt.error?.message, /SHA-256 mismatch/);
  assert.equal(receipt.invocation?.workingDirectory, 'repository root');
  assert.deepEqual(
    receipt.invocation?.command,
    ['node', 'tools/export-v11-grpo-adapter.js', ...receipt.invocation.argv]
  );
  assert.equal(receipt.claimBoundary?.adapterInferenceCorrectness, 'Not established.');
} finally {
  rmSync(tempDir, { recursive: true, force: true });
}

console.log('export-v11-grpo-adapter.test: ok');
