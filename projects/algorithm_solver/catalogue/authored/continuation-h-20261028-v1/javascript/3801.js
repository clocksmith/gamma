"use strict";
function solve(lists) {
const n=lists.length,size=1<<n,lengths=new Int32Array(size),medians=Array(size).fill(0),tagged=[];for(let i=0;i<n;i++)for(const value of lists[i])tagged.push([value,1<<i]);tagged.sort((a,b)=>a[0]-b[0]);for(let mask=1;mask<size;mask++){const bit=mask&-mask,index=31-Math.clz32(bit);lengths[mask]=lengths[mask^bit]+lists[index].length;const target=Math.floor((lengths[mask]-1)/2);let seen=0;for(const [value,origin] of tagged)if(mask&origin){if(seen===target){medians[mask]=value;break;}seen++;}}const dp=Array(size).fill(0);for(let mask=1;mask<size;mask++){if((mask&(mask-1))===0)continue;const anchor=mask&-mask;let best=Infinity;for(let subset=(mask-1)&mask;subset;subset=(subset-1)&mask)if(subset&anchor){const other=mask^subset;best=Math.min(best,dp[subset]+dp[other]+lengths[mask]+Math.abs(medians[subset]-medians[other]));}dp[mask]=best;}return dp[size-1];
}
function minMergeCost(lists) { return solve(lists); }
module.exports=solve;
module.exports.minMergeCost=minMergeCost;
