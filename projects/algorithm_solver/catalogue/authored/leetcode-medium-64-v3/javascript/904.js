'use strict';

// 904. Fruit Into Baskets: maintain the longest window containing at most two values.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(fruits) {
  const counts = new Map();
  let left = 0;
  let best = 0;
  for (let right = 0; right < fruits.length; right += 1) {
    const value = fruits[right];
    counts.set(value, (counts.get(value) || 0) + 1);
    while (counts.size > 2) {
      const outgoing = fruits[left];
      const remaining = counts.get(outgoing) - 1;
      if (remaining === 0) counts.delete(outgoing);
      else counts.set(outgoing, remaining);
      left += 1;
    }
    best = Math.max(best, right - left + 1);
  }
  return best;
}

const totalFruit = solve;
class Solution {
  totalFruit(fruits) { return solve(fruits); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, totalFruit };
