function solve(nums){let answer=0;for(let l=0;l<nums.length;l++){const seen=new Set();let total=0;for(let r=l;r<nums.length;r++){total+=nums[r];seen.add(nums[r]);if(seen.has(total))answer++;}}return answer;}

var centeredSubarrays = solve;
module.exports = solve;
