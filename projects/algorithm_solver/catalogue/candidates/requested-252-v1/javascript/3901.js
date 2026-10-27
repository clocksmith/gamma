'use strict';

// 3901. Good Subsequence Queries.
// Specification: https://leetcode.com/problems/good-subsequence-queries/description/
// Segment tree of whole GCD and exact-one-deletion GCD sets; O((n+q log n)*D log V) time, O(n*D) space, D=O(log V). Inputs are preserved.
function solve(nums, p, queries) {
  function gcd(a, b) { while (b !== 0) [a, b] = [b, a % b]; return a; }
  let width = 1;
  while (width < nums.length) width *= 2;
  const whole = new Int32Array(2 * width);
  const deleted = Array.from({ length: 2 * width }, () => []);
  function pull(node) {
    const left = 2 * node;
    const right = left + 1;
    whole[node] = gcd(whole[left], whole[right]);
    const possibilities = new Set();
    for (const value of deleted[left]) possibilities.add(gcd(value, whole[right]));
    for (const value of deleted[right]) possibilities.add(gcd(whole[left], value));
    deleted[node] = [...possibilities];
  }
  for (let index = 0; index < nums.length; index++) {
    whole[width + index] = nums[index] % p === 0 ? nums[index] : 0;
    deleted[width + index] = [0];
  }
  for (let node = width - 1; node > 0; node--) pull(node);
  let answer = 0;
  for (const [index, value] of queries) {
    let node = width + index;
    whole[node] = value % p === 0 ? value : 0;
    while (node > 1) { node = Math.floor(node / 2); pull(node); }
    if (deleted[1].includes(p)) answer++;
  }
  return answer;
}

if (typeof module !== 'undefined') module.exports = { solve };
