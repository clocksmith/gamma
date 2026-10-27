/**
 * 4075. Longest Resilient Subarray I
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/longest-resilient-subarray-i/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4075.Longest%20Resilient%20Subarray%20I/README_EN.md
 * Complexity: O(n+R log k) time, O(1) space, R equal-residue runs.
 * Every deletion leaving a divisible sum forces all residues to agree. For run residue a, valid lengths satisfy L=1 modulo k/gcd(k,a). Select the largest such length within each run. Inputs preserved.
 */

function solve(nums,k) {
  function gcd(a,b){while(b){const c=a%b;a=b;b=c;}return a;}
  let answer=1,left=0;
  while(left<nums.length) {
    const residue=nums[left]%k;let right=left+1;
    while(right<nums.length && nums[right]%k===residue)right++;
    const length=right-left,period=k/gcd(k,residue);
    answer=Math.max(answer,length-(length-1)%period);left=right;
  }
  return answer;
}

function resilientSubarray(nums, k) {
  return solve(nums, k);
}

class Solution {
  resilientSubarray(nums, k) {
    return solve(nums, k);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, resilientSubarray, Solution };
}
