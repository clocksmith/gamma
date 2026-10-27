'use strict';

// 4032. Longest Subarray With at Most K Distinct Prime Factors.
// Specification: https://leetcode.com/problems/longest-subarray-with-at-most-k-distinct-prime-factors/description/
// O(V log log V+n log V) time and O(V+n log V) space; cached distinct factors and a sliding window. Inputs are preserved.
function solve(nums, k) {
  let maximum = 2;
  for (const value of nums) maximum = Math.max(maximum, value);
  const smallest = new Int32Array(maximum + 1);
  for (let prime = 2; prime <= maximum; prime++) {
    if (smallest[prime] !== 0) continue;
    smallest[prime] = prime;
    for (let multiple = prime * prime; multiple <= maximum; multiple += prime) {
      if (smallest[multiple] === 0) smallest[multiple] = prime;
    }
  }
  const cache = new Map();
  function factors(value) {
    if (cache.has(value)) return cache.get(value);
    const result = [];
    let remaining = value;
    while (remaining > 1) {
      const prime = smallest[remaining];
      result.push(prime);
      while (remaining % prime === 0) remaining /= prime;
    }
    cache.set(value, result);
    return result;
  }
  const counts = new Map();
  let left = 0;
  let answer = 0;
  for (let right = 0; right < nums.length; right++) {
    for (const prime of factors(nums[right])) counts.set(prime, (counts.get(prime) || 0) + 1);
    while (counts.size > k) {
      for (const prime of factors(nums[left++])) {
        const count = counts.get(prime) - 1;
        if (count === 0) counts.delete(prime); else counts.set(prime, count);
      }
    }
    answer = Math.max(answer, right - left + 1);
  }
  return answer;
}

if (typeof module !== 'undefined') module.exports = { solve };
