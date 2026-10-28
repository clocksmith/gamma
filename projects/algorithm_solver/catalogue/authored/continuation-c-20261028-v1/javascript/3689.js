function solve(nums,k){let hi=0,lo=Infinity;for(const v of nums){hi=Math.max(hi,v);lo=Math.min(lo,v);}return (hi-lo)*k;}

var maxTotalValue = solve;
module.exports = solve;
