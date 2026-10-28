function solve(nums){let first=0,second=0;for(const v of nums){const x=Math.abs(v);if(x>=first){second=first;first=x;}else if(x>second)second=x;}return 100000*first*second;}

var maxProduct = solve;
module.exports = solve;
