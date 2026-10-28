"use strict";
function solve(nums1, nums2) {
const first=new Map(),second=new Map();for(const v of nums1)first.set(v,(first.get(v)||0)+1);for(const v of nums2)second.set(v,(second.get(v)||0)+1);const keys=new Set([...first.keys(),...second.keys()]);let excess=0;for(const value of keys){const a=first.get(value)||0,b=second.get(value)||0,total=a+b;if(total%2)return -1;excess+=Math.max(0,a-total/2);}return excess;
}
function minCost(nums1, nums2) { return solve(nums1, nums2); }
module.exports=solve;
module.exports.minCost=minCost;
