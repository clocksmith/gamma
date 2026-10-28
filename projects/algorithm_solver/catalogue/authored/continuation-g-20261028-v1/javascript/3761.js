function solve(nums){const pending=new Map();let answer=nums.length+1;for(let j=0;j<nums.length;j++){const x=nums[j];if(pending.has(x))answer=Math.min(answer,j-pending.get(x));pending.set(Number(String(x).split('').reverse().join('')),j);}return answer>nums.length?-1:answer;}

var minMirrorPairDistance = solve;
module.exports = solve;
