function solve(nums){let i=nums.length-1;while(i>0&&nums[i-1]<nums[i])i--;return i;}

var minimumPrefixLength = solve;
module.exports = solve;
