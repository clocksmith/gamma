// Original implementation. Contract: https://leetcode.com/problems/make-array-non-decreasing-or-non-increasing/
"use strict";
function solve(nums){function cost(a){let dp=Array(1001).fill(0);for(const x of a){let best=Infinity;const next=[];for(let y=0;y<=1000;y++){best=Math.min(best,dp[y]);next.push(best+Math.abs(x-y));}dp=next;}return Math.min(...dp);}return Math.min(cost(nums),cost([...nums].reverse()));}
module.exports = solve;
