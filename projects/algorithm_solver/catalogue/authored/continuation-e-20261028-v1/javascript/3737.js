function solve(nums,target){let answer=0;for(let i=0;i<nums.length;i++){let count=0;for(let j=i;j<nums.length;j++){if(nums[j]===target)count++;if(2*count>j-i+1)answer++;}}return answer;}

var countMajoritySubarrays = solve;
module.exports = solve;
