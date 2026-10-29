"use strict";

function solve(ip, n) {
  const parts = ip.split(".").map(Number);
  let cur =
    (BigInt(parts[0]) << 24n) |
    (BigInt(parts[1]) << 16n) |
    (BigInt(parts[2]) << 8n) |
    BigInt(parts[3]);
  let rem = BigInt(n);
  const out = [];
  while (rem > 0n) {
    let step = cur === 0n ? 1n << 32n : cur & -cur;
    while (step > rem) step >>= 1n;
    let tz = 0;
    let tmp = step;
    while (tmp > 1n) {
      tmp >>= 1n;
      tz++;
    }
    const prefix = 32 - tz;
    const p0 = Number((cur >> 24n) & 255n);
    const p1 = Number((cur >> 16n) & 255n);
    const p2 = Number((cur >> 8n) & 255n);
    const p3 = Number(cur & 255n);
    out.push(`${p0}.${p1}.${p2}.${p3}/${prefix}`);
    cur += step;
    rem -= step;
  }
  return out;
}

function ipToCIDR(ip, n) {
  return solve(ip, n);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.ipToCIDR = ipToCIDR;
