"use strict";
function solve(nums,k){const q=[[0,0]];let head=0,prefix=0,best=nums.length+1;
 for(let i=1;i<=nums.length;i++){prefix+=nums[i-1];while(head<q.length&&prefix-q[head][1]>=k){best=Math.min(best,i-q[head][0]);head++;}while(head<q.length&&q[q.length-1][1]>=prefix)q.pop();q.push([i,prefix]);}
 return best<=nums.length?best:-1;
}

function shortestSubarray(nums, k) { return solve(nums, k); }
module.exports=solve;
module.exports.shortestSubarray=shortestSubarray;
