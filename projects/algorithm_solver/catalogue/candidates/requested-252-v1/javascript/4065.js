/**
 * 4065. Rearrange Array by Removing Distinct Values
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/rearrange-array-by-removing-distinct-values/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4065.Rearrange%20Array%20by%20Removing%20Distinct%20Values/README_EN.md
 * Complexity: O(n+U log U) time, O(n+U) space.
 * Each round emits one occurrence of every remaining distinct value, ascending; exhausted values are removed from the active list. Original input is preserved.
 */

function solve(nums) {
  const counts=new Map();for(const value of nums)counts.set(value,(counts.get(value)||0)+1);
  let active=Array.from(counts.keys()).sort((a,b)=>a-b);const answer=[];
  while(active.length) {
    const next=[];
    for(const value of active){answer.push(value);counts.set(value,counts.get(value)-1);if(counts.get(value)>0)next.push(value);}
    active=next;
  }
  return answer;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
