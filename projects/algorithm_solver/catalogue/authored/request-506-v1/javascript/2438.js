// Original candidate implementation. Contract: https://leetcode.com/problems/range-product-queries-of-powers/
"use strict";
function solve(n,queries){const prefix=[0];for(let bit=0;2**bit<=n;bit++)if(Math.floor(n/2**bit)%2)prefix.push(prefix[prefix.length-1]+bit);const power=[1];for(let i=0;i<prefix[prefix.length-1];i++)power.push(power[i]*2%1000000007);return queries.map(([l,r])=>power[prefix[r+1]-prefix[l]]);}
module.exports = solve;
