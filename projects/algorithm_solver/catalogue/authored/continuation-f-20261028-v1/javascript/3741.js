"use strict";
function solve(nums) {
const recent=new Map();let best=2*nums.length+1;for(let i=0;i<nums.length;i++){const pair=recent.get(nums[i])||[];if(pair.length===2)best=Math.min(best,2*(i-pair[0]));recent.set(nums[i],pair.concat(i).slice(-2));}return best<=2*nums.length?best:-1;
}
function minimumDistance(nums) { return solve(nums); }
module.exports=solve;
module.exports.minimumDistance=minimumDistance;
