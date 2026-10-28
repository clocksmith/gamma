"use strict";
function solve(nums) {
const n=nums.length,left=Array(n).fill(1),right=Array(n).fill(1);function sign(a,b){return b>a?1:b<a?-1:0;}for(let i=1;i<n;i++){const direction=sign(nums[i-1],nums[i]);if(direction)left[i]=i>=2&&direction===-sign(nums[i-2],nums[i-1])?left[i-1]+1:2;}for(let i=n-2;i>=0;i--){const direction=sign(nums[i],nums[i+1]);if(direction)right[i]=i+2<n&&direction===-sign(nums[i+1],nums[i+2])?right[i+1]+1:2;}let answer=1;for(const value of left)answer=Math.max(answer,value);for(let removed=1;removed+1<n;removed++){const bridge=sign(nums[removed-1],nums[removed+1]);if(!bridge)continue;let a=left[removed-1],b=right[removed+1];if(a>=2&&sign(nums[removed-2],nums[removed-1])===bridge)a=1;if(b>=2&&sign(nums[removed+1],nums[removed+2])===bridge)b=1;answer=Math.max(answer,a+b);}return answer;
}
function longestAlternating(nums) { return solve(nums); }
module.exports=solve;
module.exports.longestAlternating=longestAlternating;
