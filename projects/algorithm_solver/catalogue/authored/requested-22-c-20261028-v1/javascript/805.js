"use strict";
function solve(nums) {
const n=nums.length;if(n<2)return false;let total=0;for(const x of nums)total+=x;const scaled=nums.map(x=>x*n-total),half=Math.floor(n/2);function subsetSums(values){let sums=[0];for(const x of values){const size=sums.length;for(let i=0;i<size;i++)sums.push(sums[i]+x);}return sums;}const leftSums=subsetSums(scaled.slice(0,half)),rightSums=subsetSums(scaled.slice(half));for(let i=1;i<leftSums.length;i++)if(leftSums[i]===0)return true;for(let i=1;i<rightSums.length;i++)if(rightSums[i]===0)return true;const leftProper=new Set(leftSums.slice(1,leftSums.length-1));for(let i=1;i<rightSums.length;i++)if(leftProper.has(-rightSums[i]))return true;return false;
}
function splitArraySameAverage(nums) { return solve(nums); }
module.exports=solve;
module.exports.splitArraySameAverage=splitArraySameAverage;
