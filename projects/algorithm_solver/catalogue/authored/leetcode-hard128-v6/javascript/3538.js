'use strict';

// 3538. Merge Operations for Minimum Travel Time.
// Choose consecutive retained signs, carrying the preceding retained index to recover each merged time; O(n^2*k^2+n) time and O(n^2*k+n) space. Inputs are preserved.

function solve(l, n, k, position, time) {
  const prefix = [0], memo = new Map();
  for (const value of time) prefix.push(prefix[prefix.length - 1] + value);
  function visit(previous, current, remaining) {
    if (current === n - 1) return remaining === 0 ? 0 : Infinity;
    if (remaining > n - current - 2) return Infinity;
    const identity = ((previous + 1) * n + current) * (k + 1) + remaining;
    if (memo.has(identity)) return memo.get(identity);
    const rate = prefix[current + 1] - prefix[previous + 1];
    let best = Infinity;
    for (let following = current + 1; following < n && following <= current + remaining + 1; following += 1) {
      const removed = following - current - 1;
      best = Math.min(best, (position[following] - position[current]) * rate + visit(current, following, remaining - removed));
    }
    memo.set(identity, best);
    return best;
  }
  return visit(-1, 0, k);
}

const minTravelTime = solve;
class Solution {
  minTravelTime(l, n, k, position, time) { return solve(l, n, k, position, time); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minTravelTime };
