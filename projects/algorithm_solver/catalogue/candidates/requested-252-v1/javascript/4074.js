/**
 * 4074. Maximum Product Pair With Target Sum
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/maximum-product-pair-with-target-sum/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4074.Maximum%20Product%20Pair%20With%20Target%20Sum/README_EN.md
 * Complexity: O(n) expected time, O(n) space.
 * Return indices, larger value first. Equal-value pairs are forbidden even at distinct indices. Negative products remain eligible; any maximum-product tie is valid. Inputs preserved.
 */

function solve(nums,target) {
  const first=new Map();let answer=[-1,-1],best=-Infinity;
  for(let index=0;index<nums.length;index++) {
    const value=nums[index],other=target-value;
    if(other!==value && first.has(other)) {
      const product=value*other;
      if(product>best){best=product;answer=value>other?[index,first.get(other)]:[first.get(other),index];}
    }
    if(!first.has(value))first.set(value,index);
  }
  return answer;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
