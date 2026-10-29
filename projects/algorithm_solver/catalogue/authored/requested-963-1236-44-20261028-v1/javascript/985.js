"use strict";
function solve(nums,queries){const a=[...nums],out=[];let total=a.reduce((s,v)=>s+(v%2===0?v:0),0);for(const [delta,i]of queries){if(a[i]%2===0)total-=a[i];a[i]+=delta;if(a[i]%2===0)total+=a[i];out.push(total);}return out;}

function sumEvenAfterQueries(nums, queries){return solve(nums, queries);}
module.exports=solve;
module.exports.sumEvenAfterQueries=sumEvenAfterQueries;
