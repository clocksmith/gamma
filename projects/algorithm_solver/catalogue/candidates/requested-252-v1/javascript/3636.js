'use strict';

// 3636. Threshold Majority Queries.
// Specification: https://leetcode.com/problems/threshold-majority-queries/description/
// Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
// O(q log q + (n + q) sqrt(n) log n) time, O(n + q) space; exact Mo ordering and frequency-winner segment tree.
// Inputs are not modified.
// Returns the smallest value among the highest-frequency elements only when its count reaches the threshold. No randomized majority assumption. Runtime bounds remain unmeasured.

function solve(nums, queries) {
  const values = Array.from(new Set(nums)).sort((a, b) => a - b);
  const ranks = new Map(values.map((value, index) => [value, index]));
  const encoded = nums.map(value => ranks.get(value));
  const frequencies = new Int32Array(values.length);
  let capacity = 1;
  while (capacity < values.length) capacity *= 2;
  const winners = new Int32Array(2 * capacity).fill(-1);
  for (let index = 0; index < values.length; index++) winners[capacity + index] = index;
  function better(first, second) {
    if (first < 0) return second;
    if (second < 0) return first;
    if (frequencies[first] !== frequencies[second]) return frequencies[first] > frequencies[second] ? first : second;
    return Math.min(first, second);
  }
  for (let node = capacity - 1; node > 0; node--) winners[node] = better(winners[2 * node], winners[2 * node + 1]);
  function change(position, delta) {
    const rank = encoded[position];
    frequencies[rank] += delta;
    for (let node = Math.floor((capacity + rank) / 2); node > 0; node = Math.floor(node / 2)) {
      winners[node] = better(winners[2 * node], winners[2 * node + 1]);
    }
  }
  const blockSize = Math.max(1, Math.floor(Math.sqrt(nums.length)));
  const order = Array.from({ length: queries.length }, (_, index) => index);
  order.sort((a, b) => {
    const firstBlock = Math.floor(queries[a][0] / blockSize);
    const secondBlock = Math.floor(queries[b][0] / blockSize);
    if (firstBlock !== secondBlock) return firstBlock - secondBlock;
    return firstBlock % 2 === 0 ? queries[a][1] - queries[b][1] : queries[b][1] - queries[a][1];
  });
  const answers = new Array(queries.length).fill(-1);
  let left = 0, right = -1;
  for (const index of order) {
    const [start, end, threshold] = queries[index];
    while (left > start) { left--; change(left, 1); }
    while (right < end) { right++; change(right, 1); }
    while (left < start) { change(left, -1); left++; }
    while (right > end) { change(right, -1); right--; }
    const winner = winners[1];
    if (frequencies[winner] >= threshold) answers[index] = values[winner];
  }
  return answers;
}

const subarrayMajority = solve;
class Solution {
  subarrayMajority(nums, queries) { return solve(nums, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, subarrayMajority };
