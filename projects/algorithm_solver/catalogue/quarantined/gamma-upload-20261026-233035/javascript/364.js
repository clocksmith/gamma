'use strict';
// 364. Nested List Weight Sum II.
function solve(nestedList) {
  let unweighted = 0; let weighted = 0; let level = nestedList;
  while (level.length) {
    const following = [];
    for (const item of level) {
      if (item.isInteger()) unweighted += item.getInteger();
      else following.push(...item.getList());
    }
    weighted += unweighted; level = following;
  }
  return weighted;
}
const depthSumInverse = solve;
class Solution { depthSumInverse(nestedList) { return solve(nestedList); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, depthSumInverse };
