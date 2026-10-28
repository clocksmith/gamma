"use strict";
function solve(nums) {
let answer=0;for(let bit=0;bit<29;bit++){const tails=[];for(const value of nums)if(value&(2**bit)){let lo=0,hi=tails.length;while(lo<hi){const mid=Math.floor((lo+hi)/2);if(tails[mid]<value)lo=mid+1;else hi=mid;}tails[lo]=value;}answer=Math.max(answer,tails.length);}return answer;
}
function longestSubsequence(nums) { return solve(nums); }
module.exports=solve;
module.exports.longestSubsequence=longestSubsequence;
