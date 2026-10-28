"use strict";
function solve(num1, num2) {
function prefix(limit){if(limit<=0)return 0n;const digits=String(limit).split('').map(Number),memo=new Map();function visit(position,older,previous,tight){if(position===digits.length)return [1n,0n];const key=[position,older,previous,tight?1:0].join(',');if(memo.has(key))return memo.get(key);let count=0n,total=0n;const bound=tight?digits[position]:9;for(let digit=0;digit<=bound;digit++){const nextTight=tight&&digit===bound;let child,bonus=0n;if(previous===-1&&digit===0)child=visit(position+1,-1,-1,nextTight);else{if(older!==-1&&((previous>older&&previous>digit)||(previous<older&&previous<digit)))bonus=1n;child=visit(position+1,previous,digit,nextTight);}count+=child[0];total+=child[1]+child[0]*bonus;}const result=[count,total];memo.set(key,result);return result;}return visit(0,-1,-1,true)[1];}return Number(prefix(num2)-prefix(num1-1));
}
function totalWaviness(num1, num2) { return solve(num1, num2); }
module.exports=solve;
module.exports.totalWaviness=totalWaviness;
