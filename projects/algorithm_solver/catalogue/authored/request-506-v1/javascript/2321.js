/* Original candidate for LeetCode 2321. Contract: https://leetcode.com/problems/maximum-score-of-spliced-array/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n) time, O(1) space */
"use strict";
function solve(nums1,nums2){let a=0,b=0,ma=0,mb=0,s1=0,s2=0;for(let i=0;i<nums1.length;i++){const x=nums1[i],y=nums2[i];s1+=x;s2+=y;a=Math.max(0,a+y-x);b=Math.max(0,b+x-y);ma=Math.max(ma,a);mb=Math.max(mb,b);}return Math.max(s1+ma,s2+mb);}
module.exports = solve;
