"use strict";
function solve(s, cost) {
const saved=Array(26).fill(0);let total=0;for(let i=0;i<s.length;i++){saved[s.charCodeAt(i)-97]+=cost[i];total+=cost[i];}return total-Math.max(...saved);
}
function minCost(s, cost) { return solve(s, cost); }
module.exports=solve;
module.exports.minCost=minCost;
