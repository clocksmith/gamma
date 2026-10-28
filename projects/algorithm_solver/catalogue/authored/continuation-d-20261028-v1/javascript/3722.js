"use strict";
// Original development candidate; qualification pending.
function solve(s) {
let best=s;for(let width=1;width<=s.length;width++){const prefix=s.slice(0,width).split('').reverse().join('')+s.slice(width),suffix=s.slice(0,-width)+s.slice(-width).split('').reverse().join('');if(prefix<best)best=prefix;if(suffix<best)best=suffix;}return best;
}
function lexSmallest(s) { return solve(s); }
module.exports = solve;
module.exports.lexSmallest = lexSmallest;
