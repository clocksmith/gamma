'use strict';

// 1482. Minimum Number of Days to Make m Bouquets: binary search the first feasible bloom day.
// O(n log(D + 1)) time and O(1) auxiliary space for day range D; inputs are read-only.
function solve(bloomDay, m, k) {
  if (m > Math.floor(bloomDay.length / k)) return -1;

  function canMake(day) {
    let consecutive = 0;
    let bouquets = 0;
    for (const bloom of bloomDay) {
      if (bloom > day) {
        consecutive = 0;
        continue;
      }
      consecutive += 1;
      if (consecutive === k) {
        bouquets += 1;
        if (bouquets === m) return true;
        consecutive = 0;
      }
    }
    return false;
  }

  let low = bloomDay[0];
  let high = bloomDay[0];
  for (const bloom of bloomDay) {
    low = Math.min(low, bloom);
    high = Math.max(high, bloom);
  }
  while (low < high) {
    const middle = low + Math.floor((high - low) / 2);
    if (canMake(middle)) high = middle;
    else low = middle + 1;
  }
  return low;
}

const minDays = solve;
class Solution {
  minDays(bloomDay, m, k) { return solve(bloomDay, m, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minDays };
