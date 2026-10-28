function solve(nums){let previous=new Map(),answer=0;const latest=new Map();for(let r=0;r<nums.length;r++){const x=nums[r],current=new Map([[x,[r,r]]]);for(const [value,[lo,hi]] of previous){const key=value|x;if(current.has(key)){const old=current.get(key);current.set(key,[Math.min(lo,old[0]),Math.max(hi,old[1])]);}else current.set(key,[lo,hi]);}latest.set(x,r);for(const [value,[lo,hi]] of current)answer+=Math.max(0,Math.min(hi,latest.has(value)?latest.get(value):-1)-lo+1);previous=current;}return answer;}

var countGoodSubarrays = solve;
module.exports = solve;

