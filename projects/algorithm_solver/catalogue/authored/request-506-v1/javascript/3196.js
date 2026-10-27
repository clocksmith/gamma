/* Original candidate for LeetCode 3196. Contract: https://leetcode.com/problems/maximize-total-cost-of-alternating-subarrays/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n) time, O(1) space; absolute sum <= 10^14 */
"use strict";
function solve(nums){let plus=nums[0],minus=-Infinity;for(let i=1;i<nums.length;i++){let x=nums[i],p=Math.max(plus,minus)+x;minus=plus-x;plus=p;}return Math.max(plus,minus);}
module.exports = solve;
