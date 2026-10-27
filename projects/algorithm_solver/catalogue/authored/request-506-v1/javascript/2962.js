// Original implementation. Contract: https://leetcode.com/problems/count-subarrays-where-max-element-appears-at-least-k-times/
"use strict";
function solve(a,k){let mx=-Infinity;for(const x of a)mx=Math.max(mx,x);let left=0,count=0,out=0;for(const x of a){count+=x===mx;while(count>=k){count-=a[left]===mx;left++;}out+=left;}return out;}
module.exports = solve;
