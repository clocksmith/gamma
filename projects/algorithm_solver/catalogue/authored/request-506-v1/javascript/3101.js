/* Original candidate for LeetCode 3101. Contract: https://leetcode.com/problems/count-alternating-subarrays/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n) time, O(1) space */
"use strict";
function solve(nums){let ans=0,run=0,last=-1;for(const x of nums){run=x!==last?run+1:1;ans+=run;last=x;}return ans;}
module.exports = solve;
