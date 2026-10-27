// Original candidate implementation. Contract: https://leetcode.com/problems/find-substring-with-given-hash-value/
"use strict";
function solve(s,power,modulo,k,hashValue){const p=BigInt(power),m=BigInt(modulo),wanted=BigInt(hashValue);let outgoing=1n;for(let i=0;i<k;i++)outgoing=outgoing*p%m;let value=0n,answer=0;for(let i=s.length-1;i>=0;i--){value=(value*p+BigInt(s.charCodeAt(i)-96))%m;if(i+k<s.length)value=(value-BigInt(s.charCodeAt(i+k)-96)*outgoing%m+m)%m;if(i+k<=s.length&&value===wanted)answer=i;}return s.slice(answer,answer+k);}
module.exports = solve;
