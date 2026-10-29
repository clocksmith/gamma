"use strict";
function solve(nums){const values=[...nums].sort((a,b)=>a-b),n=values.length,adj=values.map((v,i)=>values.map((w,j)=>j).filter(j=>j!==i&&Number.isInteger(Math.sqrt(v+values[j])))),memo=new Map(),full=(1<<n)-1;function count(last,mask){if(mask===full)return 1;const key=mask*(n+1)+last+1;if(memo.has(key))return memo.get(key);let answer=0;for(const j of last===-1?values.map((_,i)=>i):adj[last]){if(mask&(1<<j)||j&&values[j]===values[j-1]&&!(mask&(1<<(j-1))))continue;answer+=count(j,mask|(1<<j));}memo.set(key,answer);return answer;}return count(-1,0);}

function numSquarefulPerms(nums){return solve(nums);}
module.exports=solve;
module.exports.numSquarefulPerms=numSquarefulPerms;
