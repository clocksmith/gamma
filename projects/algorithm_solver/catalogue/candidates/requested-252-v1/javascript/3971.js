'use strict';

// 3971. Maximum Total Value.
// Specification: https://leetcode.com/problems/maximum-total-value/description/
// O(n log V) time and O(1) auxiliary space; exact AP sums use BigInt in JavaScript. Inputs are preserved.
function solve(value, decay, m) {
  let low = 0;
  let high = 0;
  for (const initial of value) high = Math.max(high, initial);
  function countAbove(threshold) {
    let count = 0;
    for (let index = 0; index < value.length; index++) {
      if (value[index] > threshold) count += Math.floor((value[index] - threshold - 1) / decay[index]) + 1;
      if (count > m) return count;
    }
    return count;
  }
  while (low < high) {
    const middle = Math.floor((low + high) / 2);
    if (countAbove(middle) <= m) high = middle; else low = middle + 1;
  }
  let selected = 0;
  let total = 0n;
  const modulus = 1000000007n;
  for (let index = 0; index < value.length; index++) {
    if (value[index] <= low) continue;
    const count = Math.floor((value[index] - low - 1) / decay[index]) + 1;
    selected += count;
    const copies = BigInt(count);
    total = (total + copies * (2n * BigInt(value[index]) - (copies - 1n) * BigInt(decay[index])) / 2n) % modulus;
  }
  total = (total + BigInt(m - selected) * BigInt(low)) % modulus;
  return Number(total);
}

if (typeof module !== 'undefined') module.exports = { solve };
