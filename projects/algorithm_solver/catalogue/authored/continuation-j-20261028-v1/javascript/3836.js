"use strict";
function solve(nums1, nums2, k) {
const width=nums2.length,impossible=-Infinity;let previous=Array.from({length:width+1},()=>[0,...Array(k).fill(impossible)]);for(const first of nums1){const current=Array.from({length:width+1},()=>[0,...Array(k).fill(impossible)]);for(let j=1;j<=width;j++)for(let count=1;count<=k;count++){let best=Math.max(previous[j][count],current[j-1][count]);const diagonal=previous[j-1][count-1];if(diagonal!==impossible)best=Math.max(best,diagonal+first*nums2[j-1]);current[j][count]=best;}previous=current;}return previous[width][k];
}
function maxScore(nums1, nums2, k) { return solve(nums1, nums2, k); }
module.exports=solve;
module.exports.maxScore=maxScore;
