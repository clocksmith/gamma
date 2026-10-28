"use strict";
function solve(s, queries) {
const modulus=1000000007n,values=[0n],counts=[0],sums=[0],powers=[1n];for(const char of s){const digit=Number(char);values.push(digit?(values[values.length-1]*10n+BigInt(digit))%modulus:values[values.length-1]);counts.push(counts[counts.length-1]+(digit?1:0));sums.push(sums[sums.length-1]+digit);powers.push(powers[powers.length-1]*10n%modulus);}return queries.map(([left,right])=>{const length=counts[right+1]-counts[left],value=(values[right+1]-values[left]*powers[length]%modulus+modulus)%modulus;return Number(value*BigInt(sums[right+1]-sums[left])%modulus);});
}
function sumAndMultiply(s, queries) { return solve(s, queries); }
module.exports=solve;
module.exports.sumAndMultiply=sumAndMultiply;
