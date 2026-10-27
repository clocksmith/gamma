// Original candidate. Contract: https://leetcode.com/problems/maximum-price-to-fill-a-bag/
"use strict";
function solve(items,capacity){let total=0;for(const[p,w]of items.map(x=>x.slice()).sort((a,b)=>b[0]*a[1]-a[0]*b[1])){const used=Math.min(capacity,w);total+=p*used/w;capacity-=used;if(capacity===0)return total;}return -1;}
module.exports = solve;
