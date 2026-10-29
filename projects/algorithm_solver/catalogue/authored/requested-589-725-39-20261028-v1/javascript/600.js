"use strict";
function solve(n){const counts=[1,2];for(let i=2;i<=30;i++)counts.push(counts[i-1]+counts[i-2]);let ans=0,previous=0;for(let bit=30;bit>=0;bit--){if(Math.floor(n/2**bit)%2){ans+=counts[bit];if(previous)return ans;previous=1;}else previous=0;}return ans+1;}

function findIntegers(n){return solve(n);}
module.exports=solve;
module.exports.findIntegers=findIntegers;
