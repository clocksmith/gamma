'use strict';

// 3321. Find X-Sum of All K-Long Subarrays II.
// Compress all reachable (frequency,value) ranks and maintain order counts and weighted sums in Fenwick trees; O(n log n) time and O(n) space. Inputs are preserved.

function solve(nums, k, x) {
  const totals = new Map();
  for (const value of nums) totals.set(value, (totals.get(value) || 0) + 1);
  const pairs = [], ranks = new Map();
  for (const [value, maximum] of totals) {
    ranks.set(value, new Int32Array(maximum + 1));
    for (let count = 1; count <= maximum; count += 1) pairs.push([count, value]);
  }
  pairs.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  pairs.forEach(([count, value], index) => { ranks.get(value)[count] = index + 1; });
  const size = pairs.length, counts = new Int32Array(size + 1), sums = new Float64Array(size + 1);
  const frequency = new Map();
  let active = 0, total = 0;
  function update(rank, difference, weight) {
    for (; rank <= size; rank += rank & -rank) { counts[rank] += difference; sums[rank] += weight; }
  }
  function change(value, difference) {
    const before = frequency.get(value) || 0;
    if (before !== 0) { update(ranks.get(value)[before], -1, -before * value); active -= 1; }
    const after = before + difference;
    frequency.set(value, after);
    if (after !== 0) { update(ranks.get(value)[after], 1, after * value); active += 1; }
    total += difference * value;
  }
  let firstStep = 1;
  while (firstStep * 2 <= size) firstStep *= 2;
  function smallestSum(amount) {
    let index = 0, answer = 0;
    for (let step = firstStep; step > 0; step = Math.floor(step / 2)) {
      const following = index + step;
      if (following <= size && counts[following] <= amount) {
        amount -= counts[following]; answer += sums[following]; index = following;
      }
    }
    return answer;
  }
  const answers = [];
  for (let index = 0; index < nums.length; index += 1) {
    change(nums[index], 1);
    if (index >= k) change(nums[index - k], -1);
    if (index + 1 >= k) answers.push(total - smallestSum(Math.max(0, active - x)));
  }
  return answers;
}

const findXSum = solve;
class Solution {
  findXSum(nums, k, x) { return solve(nums, k, x); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findXSum };
