function solve(nums1){let minimum=Infinity,allEven=true;for(const x of nums1){minimum=Math.min(minimum,x);if(x%2)allEven=false;}return minimum%2===1||allEven;}

var uniformArray = solve;
module.exports = solve;

