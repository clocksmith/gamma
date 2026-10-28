"use strict";
function solve(n) {
const digits=String(n);let answer=0;for(let length=1;length<digits.length;length++)answer+=9**length;for(let i=0;i<digits.length;i++){const digit=Number(digits[i]);answer+=Math.max(0,digit-1)*9**(digits.length-i-1);if(digit===0)return answer;}return answer+1;
}
function countDistinct(n) { return solve(n); }
module.exports=solve;
module.exports.countDistinct=countDistinct;
