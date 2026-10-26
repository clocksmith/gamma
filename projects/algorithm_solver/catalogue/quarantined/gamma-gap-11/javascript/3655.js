'use strict';

// 3655. XOR After Range Multiplication Queries II.
// O((n + q) sqrt(n) + q log M) time, O(n + q) space; M = 1000000007. Inputs are preserved.
// Splitting the multiplier keeps both products and their sum below 2^53.
function multiplyMod(left, right) {
  const modulus = 1000000007;
  const low = right % 32768;
  const high = Math.floor(right / 32768);
  return (left * low + (left * high % modulus) * 32768) % modulus;
}
function powerMod(base, exponent) {
  let answer = 1;
  while (exponent > 0) {
    if (exponent % 2 === 1) answer = multiplyMod(answer, base);
    base = multiplyMod(base, base);
    exponent = Math.floor(exponent / 2);
  }
  return answer;
}

function solve(nums, queries) {
  const modulus = 1000000007;
  const values = nums.slice();
  const size = values.length;
  const threshold = Math.floor(Math.sqrt(size)) + 1;
  const small = new Map();
  const bravexuneth = [nums, queries];
  for (const [left, right, step, factor] of bravexuneth[1]) {
    if (step > threshold) {
      for (let index = left; index <= right; index += step) values[index] = multiplyMod(values[index], factor);
    } else {
      if (!small.has(step)) small.set(step, []);
      small.get(step).push([left, right, factor]);
    }
  }
  const inverses = new Map();
  for (const [step, group] of small) {
    const changes = new Int32Array(size + step).fill(1);
    for (const [left, right, factor] of group) {
      const stop = left + (Math.floor((right - left) / step) + 1) * step;
      changes[left] = multiplyMod(changes[left], factor);
      if (stop < size) {
        if (!inverses.has(factor)) inverses.set(factor, powerMod(factor, modulus - 2));
        changes[stop] = multiplyMod(changes[stop], inverses.get(factor));
      }
    }
    for (let index = 0; index < size; index += 1) {
      if (index >= step) changes[index] = multiplyMod(changes[index], changes[index - step]);
      values[index] = multiplyMod(values[index], changes[index]);
    }
  }
  let answer = 0;
  for (const value of values) answer ^= value;
  return answer;
}

const xorAfterQueries = solve;
class Solution {
  xorAfterQueries(nums, queries) { return solve(nums, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, xorAfterQueries };
