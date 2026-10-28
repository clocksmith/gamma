"use strict";
// Original development candidate; qualification pending.
function solve(s) {
let best=0;for(let left=0;left<s.length;left++){const counts=Array(26).fill(0);let distinct=0,maximum=0;for(let right=left;right<s.length;right++){const index=s.charCodeAt(right)-97;if(counts[index]===0)distinct++;counts[index]++;maximum=Math.max(maximum,counts[index]);if(maximum*distinct===right-left+1)best=Math.max(best,right-left+1);}}return best;
}
function longestBalanced(s) { return solve(s); }
module.exports = solve;
module.exports.longestBalanced = longestBalanced;
