/**
 * 4063. Longest Subarray Divisible by K with At Most One Negation I
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/longest-subarray-divisible-by-k-with-at-most-one-negation-i/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4063.Longest%20Subarray%20Divisible%20by%20K%20with%20At%20Most%20One%20Negation%20I/README_EN.md
 * Complexity: O(n+DR) expected time, O(min(k,n)+D+k) worst-case space; D distinct doubled-value residues, R distinct prefix residues.
 * Earliest prefix of each residue dominates later starts. A cursor per doubled-value residue processes each newly discovered prefix residue once, only when the negated index can lie after that prefix. Stored witnesses remain valid for all future ends. Normalize negative remainders in JavaScript. Inputs preserved.
 */

function solve(nums,k) {
  const first=new Map([[0,0]]),order=[[0,0]],cursor=new Map(),changed=new Map();
  const mod=x=>((x%k)+k)%k;
  let prefix=0,answer=0;
  for(let index=0;index<nums.length;index++) {
    const value=nums[index],adjustment=mod(2*value);
    if(adjustment!==0) {
      let p=cursor.get(adjustment)||0;
      while(p<order.length) {
        const [residue,left]=order[p],wanted=(residue+adjustment)%k;
        if(!changed.has(wanted) || left<changed.get(wanted))changed.set(wanted,left);
        p++;
      }
      cursor.set(adjustment,p);
    }
    prefix=mod(prefix+value);
    const left=Math.min(first.get(prefix)??(index+1),changed.get(prefix)??(index+1));
    answer=Math.max(answer,index+1-left);
    if(!first.has(prefix)){first.set(prefix,index+1);order.push([prefix,index+1]);}
  }
  return answer;
}

function longestSubarray(nums, k) {
  return solve(nums, k);
}

class Solution {
  longestSubarray(nums, k) {
    return solve(nums, k);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, longestSubarray, Solution };
}
