'use strict';
// Separate immutable-cost variant: retain the largest cost in each color run.
function solve(s,cost){
 let total=0,kept=0,previous='';
 for(let i=0;i<s.length;i++){
  if(s[i]===previous){total+=Math.min(kept,cost[i]);kept=Math.max(kept,cost[i]);}
  else{previous=s[i];kept=cost[i];}
 }
 return total;
}
const minCost=solve;
class Solution{minCost(s,cost){return solve(s,cost);}}
if(typeof module!=='undefined')module.exports={solve,Solution,minCost};
