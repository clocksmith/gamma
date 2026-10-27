/* Original candidate for LeetCode 2909. Contract: https://leetcode.com/problems/minimum-sum-of-mountain-triplets-ii/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n) time and space */
"use strict";
function solve(nums){let n=nums.length,right=Array(n+1).fill(Infinity);for(let i=n-1;i>=0;i--)right[i]=Math.min(nums[i],right[i+1]);let left=Infinity,ans=Infinity;for(let j=0;j<n;j++){let x=nums[j];if(left<x&&right[j+1]<x)ans=Math.min(ans,left+x+right[j+1]);left=Math.min(left,x);}return ans===Infinity?-1:ans;}
module.exports = solve;
