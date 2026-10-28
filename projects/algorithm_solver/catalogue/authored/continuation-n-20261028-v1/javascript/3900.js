"use strict";
function solve(s) {
let zero=0;for(const char of s)if(char==='0')zero++;const cap=2*Math.min(zero,s.length-zero);if(cap===0)return 0;const positions=new Map([[0,[0]]]),heads=new Map([[0,0]]);let difference=0,answer=0;for(let right=1;right<=s.length;right++){difference+=s[right-1]==='1'?1:-1;if(!positions.has(difference)){positions.set(difference,[]);heads.set(difference,0);}positions.get(difference).push(right);for(const key of [difference-2,difference,difference+2])if(positions.has(key)){const indices=positions.get(key);let head=heads.get(key);while(head<indices.length&&indices[head]<right-cap)head++;heads.set(key,head);if(head<indices.length)answer=Math.max(answer,right-indices[head]);}}return answer;
}
function longestBalanced(s) { return solve(s); }
module.exports=solve;
module.exports.longestBalanced=longestBalanced;
