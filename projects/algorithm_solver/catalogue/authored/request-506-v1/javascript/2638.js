// Original implementation. Contract: https://leetcode.com/problems/count-the-number-of-k-free-subsets/
"use strict";
function solve(nums,k){const groups=new Map();for(const x of nums){const r=x%k;if(!groups.has(r))groups.set(r,[]);groups.get(r).push(x);}let out=1;for(const g of groups.values()){g.sort((a,b)=>a-b);let skip=1,take=0,prev=null;for(const x of g){const total=skip+take;take=prev!==null&&x-prev===k?skip:total;skip=total;prev=x;}out*=skip+take;}return out;}
module.exports = solve;
