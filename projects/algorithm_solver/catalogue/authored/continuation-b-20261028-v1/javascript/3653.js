function solve(nums,queries){const values=nums.slice(),mod=1000000007;for(const [l,r,k,v] of queries)for(let i=l;i<=r;i+=k)values[i]=(values[i]*v)%mod;let answer=0;for(const x of values)answer^=x;return answer;}

var xorAfterQueries = solve;
module.exports = solve;
