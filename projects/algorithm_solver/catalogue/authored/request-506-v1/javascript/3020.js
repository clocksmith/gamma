// Original candidate. Contract: https://leetcode.com/problems/find-the-maximum-number-of-elements-in-subset/
"use strict";
function solve(nums){const c=new Map();for(const x of nums)c.set(x,(c.get(x)||0)+1);let ones=c.get(1)||0,ans=ones%2?ones:ones-1;c.delete(1);for(const x of c.keys()){let y=x,len=0;while((c.get(y)||0)>=2){len+=2;y*=y;}len+=c.has(y)?1:-1;ans=Math.max(ans,len);}return Math.max(1,ans);}
module.exports = solve;
