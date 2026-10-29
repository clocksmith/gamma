"use strict";
// Hack2Hire 6a725ef948af2ae18e995ee1 (Maximum Bounded XOR) over an INFERRED spec; qualification unknown.

function solve(lo, hi, k) {
  const memo = new Map();
  function best(bit, alo, ahi, blo, bhi, kt, lt) {
    if (bit < 0) return lt ? 0 : -1;
    const key = bit * 64 + alo * 32 + ahi * 16 + blo * 8 + bhi * 4 + kt * 2 + lt;
    if (memo.has(key)) return memo.get(key);
    const lb = (lo >> bit) & 1, hb = (hi >> bit) & 1, kb = (k >> bit) & 1;
    let result = -1;
    for (const x of [1, 0]) {
      if (kt && x > kb) continue;
      for (const abit of [0, 1]) {
        const bbit = abit ^ x;
        if ((!lt && abit > bbit) || (alo && abit < lb) || (ahi && abit > hb) || (blo && bbit < lb) || (bhi && bbit > hb)) continue;
        const sub = best(bit - 1, +(alo && abit === lb), +(ahi && abit === hb), +(blo && bbit === lb), +(bhi && bbit === hb),
                         +(kt && x === kb), +(lt || abit < bbit));
        if (sub >= 0 && x * 2 ** bit + sub > result) result = x * 2 ** bit + sub;
      }
      if (result >= 0) break;
    }
    memo.set(key, result);
    return result;
  }
  return best(30, 1, 1, 1, 1, 1, 0);
}

function maxBoundedXor(lo, hi, k) { return solve(lo, hi, k); }

module.exports = solve;
module.exports.maxBoundedXor = maxBoundedXor;
