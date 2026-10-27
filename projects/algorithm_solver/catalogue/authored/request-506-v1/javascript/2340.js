/* Original candidate for LeetCode 2340. Contract: https://leetcode.com/problems/minimum-adjacent-swaps-to-make-a-valid-array/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n) time, O(n) Python slice space / O(1) JS space */
"use strict";
function solve(nums){let a=0,b=0;for(let i=1;i<nums.length;i++){if(nums[i]<nums[a])a=i;if(nums[i]>=nums[b])b=i;}return a+nums.length-1-b-(a>b?1:0);}
module.exports = solve;
