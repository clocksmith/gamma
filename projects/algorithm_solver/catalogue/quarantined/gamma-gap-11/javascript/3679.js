'use strict';

// 3679. Minimum Discards to Balance Inventory.
// O(n) expected time and O(w) auxiliary space; inputs are preserved.
function solve(arrivals, w, m) {
  const counts = new Map();
  const kept = Array(w).fill(false);
  let answer = 0;
  for (let day = 0; day < arrivals.length; day += 1) {
    const item = arrivals[day];
    const slot = day % w;
    if (day >= w && kept[slot]) {
      const old = arrivals[day - w];
      const count = counts.get(old) - 1;
      if (count === 0) counts.delete(old);
      else counts.set(old, count);
    }
    if ((counts.get(item) || 0) === m) {
      kept[slot] = false;
      answer += 1;
    } else {
      kept[slot] = true;
      counts.set(item, (counts.get(item) || 0) + 1);
    }
  }
  return answer;
}

const minArrivalsToDiscard = solve;
class Solution {
  minArrivalsToDiscard(arrivals, w, m) { return solve(arrivals, w, m); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minArrivalsToDiscard };
