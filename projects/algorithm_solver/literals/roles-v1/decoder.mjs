// Independent decoder for roles-v1 packets (written apart from binding.py's encoder).
//   node decoder.mjs FOLDER  ->  {"<id>": "<sha256 of decoded bytes>"}; also writes FOLDER/decoded/<id>.js
// Dictionary: LTD1 (count, then length-prefixed UTF-8 entries). Packet: 'LTB1' (bind) or 'LTN1' (rename-only), width,
// sha256(dictionary), uint32 code count, packed big-endian w-bit codes.
// Slot characters are U+E000..U+E17F: role = (cp - 0xE000) >> 6 in input, output, index, queue, accumulator, other;
// ordinal = cp & 63. LTB1: after the code holding a slot's first occurrence, the name's codes follow, closed by END
// ("\x01END"); names hold no slot or END. LTN1: a slot decodes to "$$" + role letter (a r i p s v) + ordinal.
import { readFileSync, readdirSync, writeFileSync, mkdirSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { join } from 'node:path';

const END = '\x01END', LETTERS = 'aripsv';
const isSlot = (c) => { const k = c.codePointAt(0) - 0xE000; return k >= 0 && k < 64 * LETTERS.length; };
const folder = process.argv[2];
const raw = readFileSync(join(folder, 'dictionary.bin'));
const dictHash = createHash('sha256').update(raw).digest();
let off = 0;
const u32 = () => { const v = raw.readUInt32BE(off); off += 4; return v; };
if (raw.subarray(0, 4).toString('latin1') !== 'LTD1') throw new Error('dictionary magic'); off = 4;
const entries = [];
for (let n = u32(), i = 0; i < n; i++) { const len = u32(); entries.push(raw.subarray(off, off + len).toString('utf8')); off += len; }
if (off !== raw.length) throw new Error('trailing dictionary bytes');

function decode(buf) {
  const magic = buf.subarray(0, 4).toString('latin1');
  if (magic !== 'LTB1' && magic !== 'LTN1') throw new Error('packet magic');
  const width = buf[4];
  if (!buf.subarray(5, 37).equals(dictHash)) throw new Error('dictionary hash');
  if (entries.length > 2 ** width) throw new Error('dictionary exceeds width');
  const count = buf.readUInt32BE(37), payload = buf.subarray(41);
  if (payload.length !== Math.ceil(count * width / 8)) throw new Error('payload length');
  const codes = []; let acc = 0, have = 0, p = 0;
  while (codes.length < count) {
    while (have < width) { acc = (acc << 8) | payload[p++]; have += 8; }
    have -= width; codes.push(entries[(acc >> have) & ((1 << width) - 1)]); acc &= (1 << have) - 1;
    if (codes.at(-1) === undefined) throw new Error('code out of range');
  }
  let body = '', i = 0; const names = new Map();
  while (i < codes.length) {
    const piece = codes[i++];
    if (piece === END) throw new Error('END outside a declaration');
    body += piece;
    if (magic !== 'LTB1') continue;
    for (const ch of piece) {
      if (!isSlot(ch) || names.has(ch)) continue;
      let name = '';
      for (;;) {
        if (i >= codes.length) throw new Error('unterminated declaration');
        const c = codes[i++];
        if (c === END) break;
        if ([...c].some(isSlot)) throw new Error('slot inside a name');
        name += c;
      }
      if (!/^[A-Za-z_$][\w$]*$/.test(name)) throw new Error('declared name is not an identifier');
      names.set(ch, name);
    }
  }
  let out = '';
  for (const ch of body) {
    if (!isSlot(ch)) { out += ch; continue; }
    const k = ch.codePointAt(0) - 0xE000;
    out += magic === 'LTB1' ? names.get(ch) : '$$' + LETTERS[k >> 6] + (k & 63);
  }
  return out;
}

mkdirSync(join(folder, 'decoded'), { recursive: true });
const result = {};
for (const f of readdirSync(folder).filter(f => f.endsWith('.ltr')).sort()) {
  const id = f.slice(0, -4), text = decode(readFileSync(join(folder, f)));
  writeFileSync(join(folder, 'decoded', `${id}.js`), text);
  result[id] = createHash('sha256').update(Buffer.from(text, 'utf8')).digest('hex');
}
process.stdout.write(JSON.stringify(result));
