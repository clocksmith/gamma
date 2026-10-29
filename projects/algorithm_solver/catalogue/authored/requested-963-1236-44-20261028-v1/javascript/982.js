"use strict";
function solve(nums){const counts=new Float64Array(65536);for(const a of nums)for(const b of nums)counts[a&b]++;for(let bit=0;bit<16;bit++)for(let mask=0;mask<65536;mask++)if(mask&(1<<bit))counts[mask]+=counts[mask^(1<<bit)];let result=0;for(const a of nums)result+=counts[65535^a];return result;}

function countTriplets(nums){return solve(nums);}
module.exports=solve;
module.exports.countTriplets=countTriplets;
