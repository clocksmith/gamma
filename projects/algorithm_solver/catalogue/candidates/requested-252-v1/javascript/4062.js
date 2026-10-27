/**
 * 4062. Transform Array Using Pair Operations
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/transform-array-using-pair-operations/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4062.Transform%20Array%20Using%20Pair%20Operations/README_EN.md
 * Complexity: O(n) time, O(1) auxiliary space.
 * For n>=2, the operation preserves total sum and can set every coordinate using one fixed partner; equal sums are sufficient. Sums remain within exact JS Number range. Inputs preserved.
 */

function solve(source,target) {
  if(source.length!==target.length)return false;
  let difference=0;for(let i=0;i<source.length;i++)difference+=source[i]-target[i];
  return difference===0;
}

function canTransform(source, target) {
  return solve(source, target);
}

class Solution {
  canTransform(source, target) {
    return solve(source, target);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, canTransform, Solution };
}
