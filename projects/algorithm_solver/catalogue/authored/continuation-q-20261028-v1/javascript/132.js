"use strict";
function solve(s) {
const cuts=Array.from({length:s.length+1},(_,i)=>i-1);for(let center=0;center<s.length;center++)for(let [left,right] of [[center,center],[center,center+1]])while(left>=0&&right<s.length&&s[left]===s[right]){cuts[right+1]=Math.min(cuts[right+1],cuts[left]+1);left--;right++;}return cuts[s.length];
}
function minCut(s) { return solve(s); }
class Solution {minCut(s) { return solve(s); }}
module.exports=solve;
module.exports.minCut=minCut;
module.exports.Solution=Solution;
