function solve(nums){let sign=1,answer=0;for(let i=0;i<nums.length;i++){const x=nums[i];if(x%2)sign=-sign;if(i%6===5)sign=-sign;answer+=sign*x;}return answer;}

var scoreDifference = solve;
module.exports = solve;
