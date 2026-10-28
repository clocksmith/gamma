function solve(nums,target){const values=new Set();for(let i=0;i<nums.length;i++)if(nums[i]!==target[i])values.add(nums[i]);return values.size;}

var minOperations = solve;
module.exports = solve;
