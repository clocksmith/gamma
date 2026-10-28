"use strict";
// Original development candidate; qualification pending.
function solve(n) {
let states=new Map([[0,1n]]), position=0;
for(const symbol of String(n).split('').reverse()){const target=Number(symbol), next=new Map();for(const [key,count] of states){const carry=key&1, endedA=!!(key&2),endedB=!!(key&4);for(let a=endedA?0:position===0?1:0;a<=(endedA?0:9);a++)for(let b=endedB?0:position===0?1:0;b<=(endedB?0:9);b++){const value=a+b+carry;if(value%10===target){const newKey=Math.floor(value/10)|((endedA||a===0)?2:0)|((endedB||b===0)?4:0);next.set(newKey,(next.get(newKey)||0n)+count);}}}states=next;position++;}let answer=0n;for(const [key,count] of states)if(!(key&1))answer+=count;return Number(answer);
}
function countNoZeroPairs(n) { return solve(n); }
module.exports = solve;
module.exports.countNoZeroPairs = countNoZeroPairs;
