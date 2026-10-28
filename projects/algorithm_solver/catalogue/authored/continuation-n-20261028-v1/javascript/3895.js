"use strict";
function solve(nums, digit) {
let total=0;for(let value of nums)while(value){if(value%10===digit)total++;value=Math.floor(value/10);}return total;
}
function countDigitOccurrences(nums, digit) { return solve(nums, digit); }
module.exports=solve;
module.exports.countDigitOccurrences=countDigitOccurrences;
