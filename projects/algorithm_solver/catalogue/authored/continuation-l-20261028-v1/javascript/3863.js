"use strict";
function solve(s) {
let sorted=true;for(let i=1;i<s.length;i++)if(s[i-1]>s[i])sorted=false;if(sorted)return 0;if(s.length===2)return -1;let smallest='z',largest='a';for(const char of s){if(char<smallest)smallest=char;if(char>largest)largest=char;}if(s[0]===smallest||s[s.length-1]===largest)return 1;if(s.slice(0,-1).includes(smallest)||s.slice(1).includes(largest))return 2;return 3;
}
function minOperations(s) { return solve(s); }
module.exports=solve;
module.exports.minOperations=minOperations;
