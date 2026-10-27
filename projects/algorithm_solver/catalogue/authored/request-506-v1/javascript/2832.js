// Original candidate. Contract: https://leetcode.com/problems/maximal-range-that-each-element-is-maximum-in-it/
"use strict";
function solve(nums){const n=nums.length,L=Array(n).fill(-1),R=Array(n).fill(n),s=[];for(let i=0;i<n;i++){while(s.length&&nums[s[s.length-1]]<nums[i])R[s.pop()]=i;if(s.length)L[i]=s[s.length-1];s.push(i);}return L.map((x,i)=>R[i]-x-1);}
module.exports = solve;
