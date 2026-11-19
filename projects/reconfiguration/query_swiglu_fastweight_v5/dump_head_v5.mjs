// Writes a model's output matrix (lm_head) as float32 rows, for offline study of last-layer writes. CPU only:
// it reads the model's shard files through the manifest and never touches a GPU.
//
// Usage: node dump_head_v5.mjs MODEL_DIR OUT_F32
// Output: vocab x hidden float32, row-major, plus OUT_F32.json with the shape and the source tensor's identity.
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync, openSync, readSync, closeSync, appendFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { createHash } from 'node:crypto';
import { dequantizeQ4KRow } from '../../../gamma/fastweight/doppler_fastweight.mjs';

const [modelDirArg, outArg] = process.argv.slice(2);
assert.ok(modelDirArg && outArg, 'Usage: node dump_head_v5.mjs MODEL_DIR OUT_F32');
const modelDir = resolve(modelDirArg);
const manifestBytes = readFileSync(join(modelDir, 'manifest.json'));
const manifest = JSON.parse(manifestBytes);
const name = Object.keys(manifest.tensors).find(k => manifest.tensors[k].role === 'lm_head')
  ?? Object.keys(manifest.tensors).find(k => k.endsWith('embed_tokens.weight'));
const tensor = manifest.tensors[name];
const [vocab, hidden] = tensor.shape;
const dtype = String(tensor.dtype).toLowerCase();
const spans = tensor.spans ?? [{ shardIndex: tensor.shard, offset: tensor.offset, size: tensor.size }];
const total = spans.reduce((n, s) => n + s.size, 0);
const raw = Buffer.alloc(total);
let at = 0;
for (const s of spans) {
  const fd = openSync(join(modelDir, manifest.shards[s.shardIndex].filename), 'r');
  const got = readSync(fd, raw, at, s.size, s.offset);
  closeSync(fd);
  assert.equal(got, s.size, `short read in shard ${s.shardIndex}`);
  at += s.size;
}
const u8 = new Uint8Array(raw.buffer, raw.byteOffset, raw.byteLength);
const isQ4K = dtype.includes('q4_k') || dtype === 'q4k';
const rowBytes = isQ4K ? (hidden / 256) * 144 : hidden * (dtype === 'f16' ? 2 : 4);
assert.equal(total, vocab * rowBytes, `tensor bytes ${total} do not match ${vocab} rows of ${rowBytes} bytes`);
assert.ok(isQ4K || dtype === 'f32', `this tool handles Q4K and F32 output matrices; got ${tensor.dtype}`);

const out = resolve(outArg);
writeFileSync(out, Buffer.alloc(0));
const CHUNK = 8192;
for (let start = 0; start < vocab; start += CHUNK) {
  const rows = Math.min(CHUNK, vocab - start);
  const block = new Float32Array(rows * hidden);
  for (let r = 0; r < rows; r += 1) {
    const row = isQ4K
      ? dequantizeQ4KRow(u8, (start + r) * rowBytes, hidden)
      : new Float32Array(raw.buffer, raw.byteOffset + (start + r) * rowBytes, hidden);
    block.set(row, r * hidden);
  }
  appendFileSync(out, Buffer.from(block.buffer, block.byteOffset, block.byteLength));
}
writeFileSync(`${out}.json`, JSON.stringify({
  model: manifest.modelId, tensor: name, source_dtype: tensor.dtype, shape: [vocab, hidden], dtype: 'float32',
  manifest_sha256: createHash('sha256').update(manifestBytes).digest('hex'),
}) + '\n');
console.log(`wrote ${vocab} x ${hidden} float32 rows from ${name} (${tensor.dtype}) to ${out}`);
