// Original candidate. Contract: https://leetcode.com/problems/find-the-number-of-good-pairs-ii/
"use strict";
function solve(A,B,k){const c=new Map(),f=new Map();let limit=0;for(const x of A)if(x%k===0){const v=x/k;c.set(v,(c.get(v)||0)+1);limit=Math.max(limit,v);}for(const x of B)f.set(x,(f.get(x)||0)+1);let ans=0;for(const[d,freq]of f)for(let x=d;x<=limit;x+=d)ans+=freq*(c.get(x)||0);return ans;}
module.exports = solve;
