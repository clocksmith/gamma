/**
 * 3962. Maximum Subarray Sum After at Most K Swaps
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/maximum-subarray-sum-after-at-most-k-swaps/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3962.Maximum%20Subarray%20Sum%20After%20at%20Most%20K%20Swaps/README_EN.md
 * Complexity: O(n^2 log^2 n) time, O(n) space.
 * Exact interval enumeration with best improving inside/outside exchanges. n <= 1500. No candidate execution or maximum-size performance measurement. Inputs preserved; native method pending.
 */

class RankTree {
  constructor(values) {
    this.values = values;
    this.counts = new Int32Array(values.length + 1);
    this.sums = new Float64Array(values.length + 1);
    this.size = 0;
    this.total = 0;
  }
  add(index, delta) {
    const value = this.values[index];
    this.size += delta;
    this.total += delta * value;
    for (index++; index < this.counts.length; index += index & -index) {
      this.counts[index] += delta;
      this.sums[index] += delta * value;
    }
  }
  select(rank) {
    let index = 0;
    let total = 0;
    let bit = 1;
    while (bit * 2 <= this.values.length) bit *= 2;
    for (; bit > 0; bit = Math.floor(bit / 2)) {
      const candidate = index + bit;
      if (candidate < this.counts.length && this.counts[candidate] < rank) {
        rank -= this.counts[candidate];
        total += this.sums[candidate];
        index = candidate;
      }
    }
    return [this.values[index], total + rank * this.values[index]];
  }
  smallestSum(count) { return count === 0 ? 0 : this.select(count)[1]; }
}

function solve(nums, k) {
  const n = nums.length;
  let answer = nums[0];
  let running = 0;
  let positiveCount = 0;
  let positiveSum = 0;
  for (const value of nums) {
    running = Math.max(value, running + value);
    answer = Math.max(answer, running);
    if (value > 0) { positiveCount++; positiveSum += value; }
  }
  if (k === 0 || positiveCount === 0) return answer;
  if (k >= Math.min(positiveCount, n - positiveCount)) return positiveSum;
  const values = [...new Set(nums)].sort((a, b) => a - b);
  const indices = new Map(values.map((value, index) => [value, index]));
  for (let left = 0; left < n; left++) {
    const inside = new RankTree(values);
    const outside = new RankTree(values);
    for (const value of nums) outside.add(indices.get(value), 1);
    let current = 0;
    for (let right = left; right < n; right++) {
      const value = nums[right];
      inside.add(indices.get(value), 1);
      outside.add(indices.get(value), -1);
      current += value;
      let low = 0;
      let high = Math.min(k, inside.size, outside.size);
      while (low < high) {
        const middle = Math.floor((low + high + 1) / 2);
        if (inside.select(middle)[0] < outside.select(outside.size - middle + 1)[0]) low = middle;
        else high = middle - 1;
      }
      const gain = outside.total - outside.smallestSum(outside.size - low) - inside.smallestSum(low);
      answer = Math.max(answer, current + gain);
    }
  }
  return answer;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
