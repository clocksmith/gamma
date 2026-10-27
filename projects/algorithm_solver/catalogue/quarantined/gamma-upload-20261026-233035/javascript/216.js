'use strict';
// 216. Combination Sum III.
function solve(k, n) {
  const result = []; const path = [];
  function visit(start, remaining) {
    if (path.length === k) { if (remaining === 0) result.push(path.slice()); return; }
    for (let value = start; value <= 9 && value <= remaining; value += 1) {
      path.push(value); visit(value + 1, remaining - value); path.pop();
    }
  }
  visit(1, n); return result;
}
const combinationSum3 = solve;
class Solution { combinationSum3(k, n) { return solve(k, n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, combinationSum3 };
