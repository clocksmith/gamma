function solve(nums,target){let dp=new Int16Array(16384).fill(-1);dp[0]=0;for(const x of nums){const following=dp.slice();for(let value=0;value<16384;value++)if(dp[value]>=0)following[value^x]=Math.max(following[value^x],dp[value]+1);dp=following;}return dp[target]<0?-1:nums.length-dp[target];}

var minRemovals = solve;
module.exports = solve;

