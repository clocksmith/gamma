"use strict";
function solve(nums, k) {
const values=nums.filter(value=>value>=0),answer=nums.slice();if(!values.length)return answer;const shift=k%values.length;let index=0;for(let i=0;i<nums.length;i++)if(nums[i]>=0)answer[i]=values[(index++ +shift)%values.length];return answer;
}
function rotateElements(nums, k) { return solve(nums, k); }
module.exports=solve;
module.exports.rotateElements=rotateElements;
