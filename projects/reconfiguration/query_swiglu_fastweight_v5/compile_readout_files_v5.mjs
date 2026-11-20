// Compile captured CPU rows with the same fitter as the Doppler development runner.
// The private working directory holds metadata plus little-endian float32 matrices.
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync } from 'node:fs';
import { endianness } from 'node:os';
import { join } from 'node:path';
import { compileReadoutAdapter } from './readout_adapter_v5.mjs';

const dir = process.argv[2];
assert.ok(dir, 'Usage: node compile_readout_files_v5.mjs CAPTURE_DIR');
assert.equal(endianness(), 'LE');
const { nextTokens, dInter, dHidden, layer, hiddenRms } = JSON.parse(readFileSync(join(dir, 'capture.json')));
const tokens = [...new Set(nextTokens)].sort((a, b) => a - b);

function matrix(name, size) {
  const bytes = readFileSync(join(dir, name));
  assert.equal(bytes.length, size * 4, name);
  return new Float32Array(bytes.buffer, bytes.byteOffset, size);
}

const z = matrix('z.f32', nextTokens.length * dInter);
const head = matrix('head.f32', tokens.length * dHidden);
const lm = new Map(tokens.map((token, i) => [token, head.subarray(i * dHidden, (i + 1) * dHidden)]));
const spec = compileReadoutAdapter({
  rows: nextTokens.map((nextTok, i) => ({ nextTok, z: z.subarray(i * dInter, (i + 1) * dInter) })),
  layer, dInter, dHidden, getLmRow: token => lm.get(token),
  finalNormG: matrix('norm.f32', dHidden), hiddenRms,
});
const { a, b } = spec.layers.get(layer);
for (const [name, values] of [['a.f32', a], ['b.f32', b]]) {
  writeFileSync(join(dir, name), Buffer.from(values.buffer, values.byteOffset, values.byteLength));
}
