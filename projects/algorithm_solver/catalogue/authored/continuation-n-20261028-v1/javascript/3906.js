"use strict";
function solve(l, r, directions) {
const visited=new Set([0]);let position=0;for(const step of directions){position+=step==='D'?4:1;visited.add(position);}function prefix(limit){if(limit<=0)return 0;const digits=String(limit).padStart(16,'0').split('').map(Number),memo=new Map();function count(index,previous,tight){if(index===16)return 1;const key=index+','+previous+','+(tight?1:0);if(memo.has(key))return memo.get(key);const bound=tight?digits[index]:9,start=visited.has(index)?previous:0;let answer=0;for(let digit=start;digit<=bound;digit++)answer+=count(index+1,visited.has(index)?digit:previous,tight&&digit===bound);memo.set(key,answer);return answer;}return count(0,0,true)-1;}return prefix(r)-prefix(l-1);
}
function countGoodIntegersOnPath(l, r, directions) { return solve(l, r, directions); }
module.exports=solve;
module.exports.countGoodIntegersOnPath=countGoodIntegersOnPath;
