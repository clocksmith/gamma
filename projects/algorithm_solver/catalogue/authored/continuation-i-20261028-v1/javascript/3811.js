function solve(nums,target1,target2){const mod=1000000007,even=new Map([[0,1]]),odd=new Map();let prefix=0,endOdd=0,endEven=0;for(const x of nums){prefix^=x;endOdd=even.get(prefix^target1)||0;endEven=odd.get(prefix^target2)||0;odd.set(prefix,((odd.get(prefix)||0)+endOdd)%mod);even.set(prefix,((even.get(prefix)||0)+endEven)%mod);}return(endOdd+endEven)%mod;}

var alternatingXOR = solve;
module.exports = solve;
