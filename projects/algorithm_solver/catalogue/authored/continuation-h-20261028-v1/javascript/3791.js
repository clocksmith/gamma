"use strict";
function solve(low, high) {
function prefix(limit){if(limit<=0)return 0;const digits=String(limit).split('').map(Number),memo=new Map();function count(position,difference,tight){if(position===digits.length)return difference===0?1:0;const key=position+','+difference+','+(tight?1:0);if(memo.has(key))return memo.get(key);const bound=tight?digits[position]:9,sign=position%2===0?1:-1;let answer=0;for(let digit=0;digit<=bound;digit++)answer+=count(position+1,difference+sign*digit,tight&&digit===bound);memo.set(key,answer);return answer;}return count(0,0,true)-1;}return prefix(high)-prefix(low-1);
}
function countBalanced(low, high) { return solve(low, high); }
module.exports=solve;
module.exports.countBalanced=countBalanced;
