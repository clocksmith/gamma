/**
 * 4036. Lexicographically Largest String After Pair Transformations
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/lexicographically-largest-string-after-pair-transformations/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4036.Lexicographically%20Largest%20String%20After%20Pair%20Transformations/README_EN.md
 * Complexity: O(26n + output length) time, output-sized space.
 * Letter weight is 2^index. Only z may repeat after greedy decomposition; zz is not merged. Inputs preserved.
 */

function solve(nums) {
  return nums.map(value=>{
    const result=[];
    for(let bit=25;bit>=0;bit--) {
      const unit=2**bit,count=Math.floor(value/unit);
      result.push(String.fromCharCode(97+bit).repeat(count));value%=unit;
    }
    return result.join('');
  });
}

function largestString(nums) {
  return solve(nums);
}

class Solution {
  largestString(nums) {
    return solve(nums);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, largestString, Solution };
}
