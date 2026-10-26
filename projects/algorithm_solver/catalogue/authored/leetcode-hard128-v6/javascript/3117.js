'use strict';

// 3117. Minimum Sum of Values by Dividing Array.
// Rolling DP over segment number and distinct suffix-AND values; O(n*m*B) time and O(m*B) space. Inputs are preserved.

function solve(nums, andValues) {
  const m = andValues.length;
  let states = Array.from({ length: m + 1 }, () => new Map()); states[0].set(-1, 0);
  function retain(map, key, price) { if (!map.has(key) || price < map.get(key)) map.set(key, price); }
  for (const value of nums) {
    const following = Array.from({ length: m + 1 }, () => new Map());
    for (let part = 0; part < m; part += 1) {
      for (const [previous, price] of states[part]) {
        const current = previous & value, target = andValues[part];
        if ((current & target) !== target) continue;
        retain(following[part], current, price);
        if (current === target) retain(following[part + 1], -1, price + value);
      }
    }
    states = following;
  }
  return states[m].has(-1) ? states[m].get(-1) : -1;
}

const minimumValueSum = solve;
class Solution {
  minimumValueSum(nums, andValues) { return solve(nums, andValues); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumValueSum };
