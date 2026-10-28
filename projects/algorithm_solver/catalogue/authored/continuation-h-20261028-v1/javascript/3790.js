"use strict";
function solve(k) {
if(k%2===0||k%5===0)return -1;let remainder=0;for(let length=1;length<=k;length++){remainder=(remainder*10+1)%k;if(remainder===0)return length;}return -1;
}
function minAllOneMultiple(k) { return solve(k); }
module.exports=solve;
module.exports.minAllOneMultiple=minAllOneMultiple;
