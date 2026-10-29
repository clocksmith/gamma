"use strict";
// Hack2Hire 68ac67eb1bf7d2097f647efe (Randomly Partition Array) over an INFERRED spec; qualification unknown.

function solve(nums, k, randomInts) {
  const shuffled = nums.slice();
  const n = shuffled.length;
  let step = 0;
  for (let i = n - 1; i > 0; i--) {
    const j = randomInts[step++] % (i + 1);
    const t = shuffled[i]; shuffled[i] = shuffled[j]; shuffled[j] = t;
  }
  const size = n / k;
  const out = [];
  for (let s = 0; s < k; s++) out.push(shuffled.slice(s * size, (s + 1) * size));
  return out;
}

function randomPartition(nums, k, randomInts) { return solve(nums, k, randomInts); }

module.exports = solve;
module.exports.randomPartition = randomPartition;
