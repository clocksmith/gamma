function solve(nums) {const a=nums.map(x=>x*x).sort((x,y)=>x-y);let answer=0;for(let i=0;i<a.length;i++)answer+=(i<Math.floor(a.length/2)?-a[i]:a[i]);return answer;}

var maxAlternatingSum = solve;
module.exports = solve;
