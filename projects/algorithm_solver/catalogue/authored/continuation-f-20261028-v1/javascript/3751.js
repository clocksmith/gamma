"use strict";
function solve(num1, num2) {
let answer=0;for(let value=num1;value<=num2;value++){const digits=String(value);for(let i=1;i+1<digits.length;i++)if((digits[i]>digits[i-1]&&digits[i]>digits[i+1])||(digits[i]<digits[i-1]&&digits[i]<digits[i+1]))answer++;}return answer;
}
function totalWaviness(num1, num2) { return solve(num1, num2); }
module.exports=solve;
module.exports.totalWaviness=totalWaviness;
