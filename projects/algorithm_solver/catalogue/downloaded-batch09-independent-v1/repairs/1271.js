'use strict';
// Provisional decimal-string repair. Decimal input <= 1e12 is exact in Number.
function solve(num){const text=Number(num).toString(16).toUpperCase();return /[23456789]/.test(text)?'ERROR':text.replace(/0/g,'O').replace(/1/g,'I');}
const toHexspeak=solve;
class Solution{toHexspeak(num){return solve(num);}}
module.exports={solve,Solution,toHexspeak};
