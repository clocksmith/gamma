/**
 * 4049. Count Values With Equally Spaced Occurrences II
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/count-values-with-equally-spaced-occurrences-ii/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4049.Count%20Values%20With%20Equally%20Spaced%20Occurrences%20II/README_EN.md
 * Complexity: O(n) expected time, O(U) space.
 * Counts all occurrences; at least three are required. Input preserved.
 */

function solve(nums) {
  const records=new Map();
  for(let i=0;i<nums.length;i++) {
    const x=nums[i];
    if(!records.has(x))records.set(x,[1,i,0,true]);
    else { const r=records.get(x),gap=i-r[1];if(r[0]===1)r[2]=gap;else if(gap!==r[2])r[3]=false;r[0]++;r[1]=i; }
  }
  let answer=0;
  for(const r of records.values())if((false?r[0]===3:r[0]>=3)&&r[3])answer++;
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
