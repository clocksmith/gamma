"use strict";
// Original development candidate; qualification pending.
function solve(s, k) {
const pattern='('.repeat(k)+')'.repeat(k), prefix=Array(pattern.length).fill(0); let matched=0;
for(let i=1;i<pattern.length;i++){while(matched && pattern[i]!==pattern[matched])matched=prefix[matched-1]; if(pattern[i]===pattern[matched])matched++; prefix[i]=matched;}
const stack=[], states=[]; matched=0;
for(const char of s){while(matched && char!==pattern[matched])matched=prefix[matched-1]; if(char===pattern[matched])matched++; stack.push(char);states.push(matched);if(matched===pattern.length){stack.length-=pattern.length;states.length-=pattern.length;matched=states.length?states[states.length-1]:0;}}return stack.join('');
}
function removeSubstring(s, k) { return solve(s, k); }
module.exports = solve;
module.exports.removeSubstring = removeSubstring;
