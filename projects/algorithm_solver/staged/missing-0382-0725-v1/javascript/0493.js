'use strict';

// 493. Reverse Pairs. Count previous values strictly greater than twice the current value; do not sort inputs in place.

function _lowerBound(a, value) {
  let lo = 0;
  let hi = a.length;
  while (lo < hi) {
    const mid = Math.floor((lo + hi) / 2);
    if (a[mid] < value) lo = mid + 1;
    else hi = mid;
  }
  return lo;
}
function _upperBound(a, value) {
  let lo = 0;
  let hi = a.length;
  while (lo < hi) {
    const mid = Math.floor((lo + hi) / 2);
    if (a[mid] <= value) lo = mid + 1;
    else hi = mid;
  }
  return lo;
}


class _Fenwick {
  constructor(n) { this.tree = Array(n + 1).fill(0); }
  add(i, delta) {
    while (i < this.tree.length) { this.tree[i] += delta; i += i & -i; }
  }
  prefix(i) {
    let total = 0;
    while (i > 0) { total += this.tree[i]; i -= i & -i; }
    return total;
  }
}

function solve(nums) {
  const values = Array.from(new Set(nums)).sort((a, b) => a - b), tree = new _Fenwick(values.length);
  let answer = 0;
  for (let i = 0; i < nums.length; i += 1) {
    answer += i - tree.prefix(_upperBound(values, 2 * nums[i]));
    tree.add(_lowerBound(values, nums[i]) + 1, 1);
  }
  return answer;
}

const reversePairs = solve;
class Solution {
  reversePairs(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, reversePairs };
