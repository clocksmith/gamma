// Original candidate implementation. Contract: https://leetcode.com/problems/minimum-sum-of-squared-difference/
"use strict";
function solve(nums1,nums2,k1,k2){const a=nums1.map((v,i)=>Math.abs(v-nums2[i])),budget=k1+k2;if(a.reduce((s,v)=>s+v,0)<=budget)return 0;let lo=0,hi=0;for(const v of a)hi=Math.max(hi,v);while(lo<hi){const c=Math.floor((lo+hi)/2);let cost=0;for(const v of a)cost+=Math.max(0,v-c);if(cost<=budget)hi=c;else lo=c+1;}let spent=0,result=0;for(const v of a){spent+=Math.max(0,v-lo);result+=Math.min(v,lo)**2;}return result-(budget-spent)*(2*lo-1);}
module.exports = solve;
