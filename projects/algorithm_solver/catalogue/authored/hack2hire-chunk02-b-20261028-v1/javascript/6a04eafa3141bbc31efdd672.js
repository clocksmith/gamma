"use strict";
// Original Hack2Hire 6a04eafa3141bbc31efdd672 variant over an INFERRED specification; qualification unknown.
function solve(data, updates) {
  const flips = new Uint8Array(data.length + 1);
  for (const [left, right] of updates) { flips[left - 1] ^= 1; flips[right] ^= 1; }
  const out = new Array(data.length);
  let parity = 0;
  for (let i = 0; i < data.length; i++) { parity ^= flips[i]; out[i] = parity ? -data[i] : data[i]; }
  for (let i = 0; i < out.length; i++) if (out[i] === 0) out[i] = 0;
  return out;
}
function applyRangeNegations(data, updates) { return solve(data, updates); }
module.exports = solve;
module.exports.applyRangeNegations = applyRangeNegations;
