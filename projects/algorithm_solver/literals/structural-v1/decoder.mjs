// Independent decoder for structural-v1 typed packets (written apart from typed.py's encoder).
//   node decoder.mjs FOLDER  ->  {"<id>": "<sha256 of decoded bytes>"} for every FOLDER/<id>.ltt
// Dictionary: LTD1 (count, then length-prefixed UTF-8 codes) and optional LTC1 (JSON component definitions).
// Packet: 'LTT1', width, sha256(dictionary), uint32 code count, packed big-endian w-bit codes.
import { readFileSync, readdirSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { join } from 'node:path';

const DEPTH = 8, IDENT = /^[A-Za-z_$][A-Za-z0-9_$]*$/;
const folder = process.argv[2];
const raw = readFileSync(join(folder, 'dictionary.bin'));
const dictHash = createHash('sha256').update(raw).digest();

let off = 0;
const u32 = () => { const v = raw.readUInt32BE(off); off += 4; return v; };
if (raw.subarray(0, 4).toString('latin1') !== 'LTD1') throw new Error('dictionary magic'); off = 4;
const entries = [];
for (let n = u32(), i = 0; i < n; i++) { const len = u32(); entries.push(raw.subarray(off, off + len).toString('utf8')); off += len; }
const defs = {};
if (off < raw.length) {
  if (raw.subarray(off, off + 4).toString('latin1') !== 'LTC1') throw new Error('component block magic'); off += 4;
  const len = u32(); for (const d of JSON.parse(raw.subarray(off, off + len).toString('utf8'))) defs[d.id] = d; off += len;
}
if (off !== raw.length) throw new Error('trailing dictionary bytes');

function pieces(t) {
  const out = []; const re = /\$\{([A-Z])\}/g; let last = 0, m;
  while ((m = re.exec(t))) { if (m.index > last) out.push({ fixed: t.slice(last, m.index) }); out.push({ hole: m[1] }); last = re.lastIndex; }
  if (last < t.length) out.push({ fixed: t.slice(last) });
  return out;
}

function decode(buf) {
  if (buf.subarray(0, 4).toString('latin1') !== 'LTT1') throw new Error('packet magic');
  const width = buf[4];
  if (!buf.subarray(5, 37).equals(dictHash)) throw new Error('dictionary hash');
  const count = buf.readUInt32BE(37), payload = buf.subarray(41);
  if (entries.length > 2 ** width) throw new Error('dictionary exceeds width');
  const codes = [];
  let acc = 0n, have = 0, p = 0;
  while (codes.length < count) {
    while (have < width) { if (p >= payload.length) throw new Error('short payload'); acc = (acc << 8n) | BigInt(payload[p++]); have += 8; }
    have -= width; codes.push(entries[Number((acc >> BigInt(have)) & ((1n << BigInt(width)) - 1n))]); acc &= (1n << BigInt(have)) - 1n;
  }
  if (p !== payload.length || acc !== 0n) throw new Error('trailing payload bits');
  let k = 0;
  const next = () => { if (k >= codes.length) throw new Error('truncated stream'); return codes[k++]; };
  function sequence(depth, top) {
    let out = '';
    for (;;) {
      if (top && k === codes.length) return out;
      const c = next();
      if (c === undefined) throw new Error('code out of range');
      if (c === '\x01END') { if (top) throw new Error('END at top level'); return out; }
      if (!c.startsWith('\x01')) { out += c; continue; }
      const d = defs[c.slice(1)]; if (!d) throw new Error('unknown component ' + c);
      if (depth + 1 > DEPTH) throw new Error('nesting limit');
      const parts = pieces(d.template), seen = {};
      for (const part of parts) {
        if (!part.hole || part.hole in seen) continue;
        if (d.holes[part.hole] === 'id') {
          const v = next(); if (v.startsWith('\x01') || !IDENT.test(v)) throw new Error('id operand is not an identifier literal'); seen[part.hole] = v;
        } else seen[part.hole] = sequence(depth + 1, false);
      }
      for (const part of parts) out += part.fixed !== undefined ? part.fixed : seen[part.hole];
    }
  }
  return sequence(0, true);
}

const result = {};
for (const f of readdirSync(folder).filter(f => f.endsWith('.ltt')).sort()) {
  result[f.slice(0, -4)] = createHash('sha256').update(Buffer.from(decode(readFileSync(join(folder, f))), 'utf8')).digest('hex');
}
process.stdout.write(JSON.stringify(result));
