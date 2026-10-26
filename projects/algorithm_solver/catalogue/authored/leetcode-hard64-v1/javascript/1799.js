'use strict';

// 1799. Maximize Score After N Operations: pair GCD preprocessing and subset dynamic programming.
// O(n^2 * 2^n + n^2*log M) time and O(2^n + n^2) space. Inputs are preserved.
function solve(nums) {
  const length = nums.length;
  function gcd(first, second) {
    while (second !== 0) [first, second] = [second, first % second];
    return first;
  }
  const common = Array.from({ length }, () => new Int32Array(length));
  for (let first = 0; first < length; first += 1) {
    for (let second = first + 1; second < length; second += 1) common[first][second] = gcd(nums[first], nums[second]);
  }
  const size = 1 << length;
  const count = new Uint8Array(size);
  for (let mask = 1; mask < size; mask += 1) count[mask] = count[mask >> 1] + (mask & 1);
  const best = new Float64Array(size).fill(-1);
  best[0] = 0;
  for (let mask = 0; mask < size; mask += 1) {
    if (count[mask] % 2 !== 0 || best[mask] < 0) continue;
    const operation = count[mask] / 2 + 1;
    for (let first = 0; first < length; first += 1) {
      if (mask & (1 << first)) continue;
      for (let second = first + 1; second < length; second += 1) {
        if (mask & (1 << second)) continue;
        const following = mask | (1 << first) | (1 << second);
        best[following] = Math.max(best[following], best[mask] + operation * common[first][second]);
      }
    }
  }
  return best[size - 1];
}

const maxScore = solve;
class Solution {
  maxScore(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxScore };
