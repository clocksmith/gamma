// Original candidate. Contract: https://leetcode.com/problems/minimum-cost-to-separate-sentence-into-rows/
"use strict";
function solve(sentence,k){const a=sentence.split(' '),n=a.length,d=Array(n+1).fill(Infinity);d[n]=0;for(let i=n-1;i>=0;i--){let len=-1;for(let j=i;j<n;j++){len+=1+a[j].length;if(len>k)break;d[i]=Math.min(d[i],j===n-1?0:(k-len)**2+d[j+1]);}}return d[0];}
module.exports = solve;
