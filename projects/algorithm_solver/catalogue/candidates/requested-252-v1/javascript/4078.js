/**
 * 4078. Three Fibonacci Sum
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/three-fibonacci-sum/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4078.Three%20Fibonacci%20Sum/README_EN.md
 * Complexity: O(log n) time, O(1) space.
 * F_i+F_(i+1)+F_(i+2)=2F_(i+2); the final term must be a positive Fibonacci number. No global precomputation.
 */

function solve(n) {
  if(n%2)return false;
  const target=n/2;let a=0,b=1;
  while(b<target){const next=a+b;a=b;b=next;}
  return b===target;
}

function threeFibonacciSum(n) {
  return solve(n);
}

class Solution {
  threeFibonacciSum(n) {
    return solve(n);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, threeFibonacciSum, Solution };
}
