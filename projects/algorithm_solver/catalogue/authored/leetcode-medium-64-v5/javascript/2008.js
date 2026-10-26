'use strict';

// 2008. Maximum Earnings From Taxi: schedule rides by finish point using binary search over prior earnings.
// O(r * log(r + 1)) time and O(r) auxiliary space, with r rides; inputs are read-only.
function solve(n, rides) {
  const ordered = rides.slice().sort((a, b) => a[1] - b[1]);
  const ends = [0];
  const earnings = [0];
  for (const [start, end, tip] of ordered) {
    let low = 0;
    let high = ends.length;
    while (low < high) {
      const middle = Math.floor((low + high) / 2);
      if (ends[middle] <= start) low = middle + 1;
      else high = middle;
    }
    const candidate = earnings[low - 1] + end - start + tip;
    ends.push(end);
    earnings.push(Math.max(earnings[earnings.length - 1], candidate));
  }
  return earnings[earnings.length - 1];
}

const maxTaxiEarnings = solve;
class Solution {
  maxTaxiEarnings(n, rides) { return solve(n, rides); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxTaxiEarnings };
