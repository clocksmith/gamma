"use strict";
function solve(s, t, flipCost, swapCost, crossCost) {
let a=0,b=0;for(let i=0;i<s.length;i++)if(s[i]!==t[i]){if(s[i]==='0')a++;else b++;}const paired=Math.min(a,b),remaining=Math.abs(a-b);return paired*Math.min(swapCost,2*flipCost)+Math.floor(remaining/2)*Math.min(crossCost+swapCost,2*flipCost)+(remaining%2)*flipCost;
}
function minimumCost(s, t, flipCost, swapCost, crossCost) { return solve(s, t, flipCost, swapCost, crossCost); }
module.exports=solve;
module.exports.minimumCost=minimumCost;
