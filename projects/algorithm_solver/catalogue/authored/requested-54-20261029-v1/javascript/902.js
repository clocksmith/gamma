"use strict";
function solve(digits,n){const s=String(n),count=digits.length;let ans=0;for(let size=1;size<s.length;size++)ans+=count**size;
 for(let i=0;i<s.length;i++){ans+=digits.filter(d=>d<s[i]).length*count**(s.length-i-1);if(!digits.includes(s[i]))return ans;}return ans+1;
}

function atMostNGivenDigitSet(digits, n) { return solve(digits, n); }
module.exports=solve;
module.exports.atMostNGivenDigitSet=atMostNGivenDigitSet;
