function solve(nums,k){if(nums.length%k)return false;const counts=new Map();for(const x of nums){const next=(counts.get(x)||0)+1;if(next>nums.length/k)return false;counts.set(x,next);}return true;}

var partitionArray = solve;
module.exports = solve;
