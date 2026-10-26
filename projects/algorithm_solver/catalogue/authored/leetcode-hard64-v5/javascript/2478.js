'use strict';

// 2478. Number of Beautiful Partitions. Prefix-summed dynamic programming over admissible boundaries; O(n*k) time and O(n) space. Inputs are preserved.

function solve(s, k, minLength) {
  const modulus = 1000000007;
  const size = s.length;
  const prime = new Set(['2', '3', '5', '7']);
  if (k * minLength > size || !prime.has(s[0]) || prime.has(s[size - 1])) return 0;
  const boundary = Array(size + 1).fill(false);
  boundary[0] = true;
  boundary[size] = true;
  for (let index = 1; index < size; index += 1) boundary[index] = !prime.has(s[index - 1]) && prime.has(s[index]);
  let previous = Array(size + 1).fill(0);
  previous[0] = 1;
  for (let part = 0; part < k; part += 1) {
    const current = Array(size + 1).fill(0);
    let running = 0;
    for (let end = minLength; end <= size; end += 1) {
      const start = end - minLength;
      if (boundary[start]) running = (running + previous[start]) % modulus;
      if (boundary[end]) current[end] = running;
    }
    previous = current;
  }
  return previous[size];
}

const beautifulPartitions = solve;
class Solution {
  beautifulPartitions(s, k, minLength) { return solve(s, k, minLength); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, beautifulPartitions };
