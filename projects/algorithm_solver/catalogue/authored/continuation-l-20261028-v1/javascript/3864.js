"use strict";
function solve(s, encCost, flatCost) {
const prefix=[0];for(const char of s)prefix.push(prefix[prefix.length-1]+(char==='1'?1:0));function cost(left,right){const count=prefix[right]-prefix[left];if(count===0)return flatCost;const length=right-left,own=length*count*encCost;if(length%2)return own;const middle=(left+right)/2;return Math.min(own,cost(left,middle)+cost(middle,right));}return cost(0,s.length);
}
function minCost(s, encCost, flatCost) { return solve(s, encCost, flatCost); }
module.exports=solve;
module.exports.minCost=minCost;
