"use strict";
// Hack2Hire 6a330e686849fecc81440a3c (Prefix Frequency Partition) over an INFERRED spec; qualification unknown.

function solve(s) {
  const n = s.length, pre = new Int32Array(26 * (n + 1)), present = new Uint8Array(26);
  for (let i = 0; i < n; i++) {
    const c = s.charCodeAt(i) - 65, base = 26 * i;
    pre.copyWithin(base + 26, base, base + 26);
    pre[base + 26 + c]++;
    present[c] = 1;
  }
  const letters = [];
  for (let c = 0; c < 26; c++) if (present[c]) letters.push(c);
  const out = [];
  for (let size = 1; size <= n; size++) {
    if (n % size) continue;
    const want = letters.map((c) => pre[26 * size + c]);
    let ok = true;
    for (let k = 2; ok && k <= n / size; k++) {
      const off = 26 * k * size;
      for (let j = 0; j < letters.length; j++) {
        if (pre[off + letters[j]] !== k * want[j]) { ok = false; break; }
      }
    }
    if (ok) out.push(size);
  }
  return out;
}

function validPrefixLengths(s) { return solve(s); }

module.exports = solve;
module.exports.validPrefixLengths = validPrefixLengths;
