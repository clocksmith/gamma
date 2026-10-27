'use strict';

// 4055. Count Shadow Pairs II.
// Specification: https://leetcode.com/problems/count-shadow-pairs-ii/description/
// O(n log^2 n) time and O(n) peak auxiliary space; divide-and-conquer with exact open-value-range blockers. Inputs are preserved.
class CountTree {
  constructor(size) { this.size = size; this.tree = new Int32Array(size + 1); }
  add(index) { for (; index <= this.size; index += index & -index) this.tree[index]++; }
  prefix(index) { let total = 0; for (; index > 0; index -= index & -index) total += this.tree[index]; return total; }
  kth(rank) {
    let index = 0;
    let bit = 1;
    while (bit * 2 <= this.size) bit *= 2;
    for (; bit >= 1; bit = Math.floor(bit / 2)) {
      const next = index + bit;
      if (next <= this.size && this.tree[next] < rank) { index = next; rank -= this.tree[next]; }
    }
    return index + 1;
  }
}

function solve(nums) {
  function count(left, right) {
    if (right - left < 2) return 0;
    const middle = Math.floor((left + right) / 2);
    let answer = count(left, middle) + count(middle, right);
    const values = [...new Set(nums.slice(left, right))].sort((a, b) => a - b);
    const ranks = new Map(values.map((value, index) => [value, index + 1]));
    let tree = new CountTree(values.length);
    const starts = [];
    let inserted = 0;
    for (let index = middle - 1; index >= left; index--) {
      const rank = ranks.get(nums[index]);
      const notGreater = tree.prefix(rank);
      const upper = notGreater < inserted ? tree.kth(notGreater + 1) : values.length + 1;
      starts.push([upper, rank]);
      tree.add(rank);
      inserted++;
    }
    tree = new CountTree(values.length);
    const ends = [];
    for (let index = middle; index < right; index++) {
      const rank = ranks.get(nums[index]);
      const lowerCount = tree.prefix(rank - 1);
      const lower = lowerCount > 0 ? tree.kth(lowerCount) : 1;
      ends.push([rank, lower]);
      tree.add(rank);
    }
    starts.sort((a, b) => b[0] - a[0]);
    ends.sort((a, b) => b[0] - a[0]);
    tree = new CountTree(values.length);
    let position = 0;
    for (const [rank, lower] of ends) {
      while (position < starts.length && starts[position][0] >= rank) tree.add(starts[position++][1]);
      answer += tree.prefix(rank - 1) - tree.prefix(lower - 1);
    }
    return answer;
  }
  return count(0, nums.length);
}

if (typeof module !== 'undefined') module.exports = { solve };
