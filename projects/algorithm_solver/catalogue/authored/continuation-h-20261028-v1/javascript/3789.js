"use strict";
function solve(cost1, cost2, costBoth, need1, need2) {
let answer=Infinity;for(const count of [0,Math.min(need1,need2),Math.max(need1,need2)])answer=Math.min(answer,count*costBoth+Math.max(0,need1-count)*cost1+Math.max(0,need2-count)*cost2);return answer;
}
function minimumCost(cost1, cost2, costBoth, need1, need2) { return solve(cost1, cost2, costBoth, need1, need2); }
module.exports=solve;
module.exports.minimumCost=minimumCost;
