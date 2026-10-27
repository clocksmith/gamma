// Original candidate. Contract: https://leetcode.com/problems/kth-smallest-amount-with-single-denomination-combination/
"use strict";
function solve(coins,k){const c=[];for(const x of coins.slice().sort((a,b)=>a-b))if(c.every(y=>x%y!==0))c.push(x);function gcd(a,b){while(b)[a,b]=[b,a%b];return a;}const terms=[];function visit(i,l,s){for(let j=i;j<c.length;j++){const v=l/gcd(l,c[j])*c[j];terms.push([v,s]);visit(j+1,v,-s);}}visit(0,1,1);let lo=1,hi=c[0]*k;while(lo<hi){const mid=Math.floor((lo+hi)/2);let count=0;for(const[v,s]of terms)count+=s*Math.floor(mid/v);if(count>=k)hi=mid;else lo=mid+1;}return lo;}
module.exports = solve;
