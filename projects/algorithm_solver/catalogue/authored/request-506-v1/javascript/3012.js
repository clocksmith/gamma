/* Original candidate for LeetCode 3012. Contract: https://leetcode.com/problems/minimize-length-of-array-using-operations/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n) time, O(1) space */
"use strict";
function solve(nums){let m=Infinity;for(const x of nums)m=Math.min(m,x);let count=0;for(const x of nums){if(x%m)return 1;if(x===m)count++;}return Math.ceil(count/2);}
module.exports = solve;
