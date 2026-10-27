/**
 * 4038. Count Integers Appearing in a Single Block
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/count-integers-appearing-in-a-single-block/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4038.Count%20Integers%20Appearing%20in%20a%20Single%20Block/README_EN.md
 * Complexity: O(n) expected time, O(distinct values) space.
 * Counts maximal blocks, not occurrences; inputs preserved.
 */

function solve(nums) {
  const blocks=new Map();
  for(let i=0;i<nums.length;i++) if(i===0 || nums[i]!==nums[i-1]) blocks.set(nums[i],(blocks.get(nums[i])||0)+1);
  let answer=0;for(const count of blocks.values()) if(count===1)answer++;
  return answer;
}

function countSpecialIntegers(nums) {
  return solve(nums);
}

class Solution {
  countSpecialIntegers(nums) {
    return solve(nums);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, countSpecialIntegers, Solution };
}
