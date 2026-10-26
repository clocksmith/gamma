'use strict';

// 2064. Minimized Maximum of Products Distributed to Any Store: binary search the smallest store limit that needs no more than n stores.
// O(m log M) time and O(1) auxiliary space for m types and maximum quantity M; inputs are read-only.
function solve(n, quantities) {
  let low = 1;
  let high = 1;
  for (const quantity of quantities) high = Math.max(high, quantity);
  while (low < high) {
    const middle = Math.floor((low + high) / 2);
    let needed = 0;
    for (const quantity of quantities) {
      needed += Math.floor((quantity + middle - 1) / middle);
      if (needed > n) break;
    }
    if (needed <= n) high = middle;
    else low = middle + 1;
  }
  return low;
}

const minimizedMaximum = solve;
class Solution {
  minimizedMaximum(n, quantities) { return solve(n, quantities); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimizedMaximum };
