"use strict";
// Original development candidate; qualification pending.
function solve(s, target) {
const counts=Array(26).fill(0);for(const char of s)counts[char.charCodeAt(0)-97]++;let matched=0;while(matched<target.length&&counts[target.charCodeAt(matched)-97]){counts[target.charCodeAt(matched)-97]--;matched++;}for(let pivot=matched;pivot>=0;pivot--){if(pivot<matched)counts[target.charCodeAt(pivot)-97]++;if(pivot===target.length)continue;for(let index=target.charCodeAt(pivot)-96;index<26;index++)if(counts[index]){counts[index]--;return target.slice(0,pivot)+String.fromCharCode(97+index)+counts.map((count,j)=>String.fromCharCode(97+j).repeat(count)).join('');}}return '';
}
function lexGreaterPermutation(s, target) { return solve(s, target); }
module.exports = solve;
module.exports.lexGreaterPermutation = lexGreaterPermutation;
