'use strict';

// 3782. Last Remaining Integer After Alternating Deletion Operations.
// O(log n) time and O(1) space; each pass retains the first number encountered and deletes the second.
function solve(n) {
  let first = 1;
  let step = 1;
  let remaining = n;
  let fromLeft = true;
  while (remaining > 1) {
    if (!fromLeft && remaining % 2 === 0) first += step;
    remaining = Math.floor((remaining + 1) / 2);
    step *= 2;
    fromLeft = !fromLeft;
  }
  return first;
}

const lastInteger = solve;
class Solution {
  lastInteger(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, lastInteger };
