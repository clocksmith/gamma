'use strict';
// 339. Nested List Weight Sum.
function solve(nestedList) {
  function visit(values, depth) {
    let total = 0;
    for (const item of values) total += item.isInteger() ? item.getInteger() * depth : visit(item.getList(), depth + 1);
    return total;
  }
  return visit(nestedList, 1);
}
const depthSum = solve;
class Solution { depthSum(nestedList) { return solve(nestedList); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, depthSum };
