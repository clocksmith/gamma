"use strict";
function solve(nums) {
let low=1,high=nums.length;for(const value of nums)high=Math.max(high,value);while(low<high){const middle=Math.floor((low+high)/2);let operations=0;for(const value of nums)operations+=Math.floor((value+middle-1)/middle);if(operations<=middle*middle)high=middle;else low=middle+1;}return low;
}
function minimumK(nums) { return solve(nums); }
module.exports=solve;
module.exports.minimumK=minimumK;
