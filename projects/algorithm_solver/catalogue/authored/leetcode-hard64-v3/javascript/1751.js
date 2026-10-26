'use strict';

// 1751. Maximum Number of Events That Can Be Attended II: event-count DP with binary-searched successors; O(n log n+n*k) time and O(n) space.

function solve(events, k) {
  const ordered = events.slice().sort((a, b) => a[0] - b[0]);
  const size = ordered.length;
  const following = Array(size).fill(size);
  for (let index = 0; index < size; index += 1) {
    let left = index + 1;
    let right = size;
    while (left < right) {
      const middle = Math.floor((left + right) / 2);
      if (ordered[middle][0] <= ordered[index][1]) left = middle + 1;
      else right = middle;
    }
    following[index] = left;
  }
  let previous = Array(size + 1).fill(0);
  for (let count = 0; count < Math.min(k, size); count += 1) {
    const current = Array(size + 1).fill(0);
    for (let index = size - 1; index >= 0; index -= 1) {
      current[index] = Math.max(current[index + 1], ordered[index][2] + previous[following[index]]);
    }
    previous = current;
  }
  return previous[0];
}

const maxValue = solve;
class Solution {
  maxValue(events, k) { return solve(events, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxValue };
