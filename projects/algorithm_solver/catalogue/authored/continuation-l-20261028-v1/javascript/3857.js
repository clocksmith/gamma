"use strict";
function solve(n) {
return n*(n-1)/2;
}
function minCost(n) { return solve(n); }
module.exports=solve;
module.exports.minCost=minCost;
