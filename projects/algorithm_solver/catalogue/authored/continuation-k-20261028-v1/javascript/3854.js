function solve(nums){if(nums.length===1)return[0,0];let best=null;for(const first of [0,1]){let operations=0,lower=-Infinity,upper=Infinity;for(let i=0;i<nums.length;i++){const x=nums[i],wrong=Number((x&1)!==((first+i)%2));operations+=wrong;lower=Math.max(lower,x-wrong);upper=Math.min(upper,x+wrong);}const result=[operations,Math.max(1,lower-upper)];if(best===null||result[0]<best[0]||(result[0]===best[0]&&result[1]<best[1]))best=result;}return best;}

var makeParityAlternating = solve;
module.exports = solve;
