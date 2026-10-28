"use strict";
function solve(s) {
let difference=0;for(const char of s)difference+=char==='a'?1:-1;return Math.abs(difference);
}
function minLengthAfterRemovals(s) { return solve(s); }
module.exports=solve;
module.exports.minLengthAfterRemovals=minLengthAfterRemovals;
