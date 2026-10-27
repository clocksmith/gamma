/**
 * 4053. Minimum Operations to Make Every Element Palindromic
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/minimum-operations-to-make-every-element-palindromic/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4053.Minimum%20Operations%20to%20Make%20Every%20Element%20Palindromic/README_EN.md
 * Complexity: O(P log P + n log P) time, O(P) space, P=200000 generated palindromes.
 * Targets are positive and must preserve input parity because each operation changes a value by two. Precomputation occurs only inside solve; inputs preserved.
 */

function solve(nums) {
  const palindromes=[[],[]];
  for(let prefix=1;prefix<=100000;prefix++) {
    const s=String(prefix),reverse=t=>t.split('').reverse().join('');
    for(const text of [s+reverse(s),s+reverse(s.slice(0,-1))]) {
      const value=Number(text);palindromes[value%2].push(value);
    }
  }
  for(const values of palindromes)values.sort((a,b)=>a-b);
  let answer=0;
  for(const value of nums) {
    const values=palindromes[value%2];let l=0,r=values.length;
    while(l<r){const m=Math.floor((l+r)/2);if(values[m]<value)l=m+1;else r=m;}
    let difference=l<values.length?values[l]-value:Infinity;
    if(l>0)difference=Math.min(difference,value-values[l-1]);
    answer+=difference/2;
  }
  return answer;
}

function minOperations(nums) {
  return solve(nums);
}

class Solution {
  minOperations(nums) {
    return solve(nums);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, minOperations, Solution };
}
