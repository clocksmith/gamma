// Original candidate implementation. Contract: https://leetcode.com/problems/maximum-prime-difference/
"use strict";
function solve(nums){const prime=Array(101).fill(true);prime[0]=prime[1]=false;for(let p=2;p<=10;p++)if(prime[p])for(let v=p*p;v<=100;v+=p)prime[v]=false;let first=-1,last=-1;for(let i=0;i<nums.length;i++)if(prime[nums[i]]){if(first<0)first=i;last=i;}return last-first;}
module.exports = solve;
