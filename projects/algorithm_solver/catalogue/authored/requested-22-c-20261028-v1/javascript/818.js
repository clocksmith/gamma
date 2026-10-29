"use strict";
function solve(target) {
const dp=new Int32Array(target+1);for(let t=1;t<=target;t++){const k=32-Math.clz32(t);if(t===(1<<k)-1){dp[t]=k;continue;}let best=k+1+dp[(1<<k)-1-t];const reached=(1<<(k-1))-1;for(let j=0;j<k-1;j++)best=Math.min(best,k+1+j+dp[t-reached+(1<<j)-1]);dp[t]=best;}return dp[target];
}
function racecar(target) { return solve(target); }
module.exports=solve;
module.exports.racecar=racecar;
