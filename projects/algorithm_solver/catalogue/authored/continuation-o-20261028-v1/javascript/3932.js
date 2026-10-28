"use strict";
function solve(l, r, k) {
function floorRoot(bound){if(bound<0)return -1;function fits(base){let value=1;for(let i=0;i<k;i++){if(base&&value>Math.floor(bound/base))return false;value*=base;}return value<=bound;}let low=0,high=bound+1;while(low+1<high){const middle=Math.floor((low+high)/2);if(fits(middle))low=middle;else high=middle;}return low;}return floorRoot(r)-floorRoot(l-1);
}
function countKthRoots(l, r, k) { return solve(l, r, k); }
module.exports=solve;
module.exports.countKthRoots=countKthRoots;
