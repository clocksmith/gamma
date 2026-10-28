"use strict";
function solve(nums) {
function gcd(a,b){while(b){const next=a%b;a=b;b=next;}return a;}const values=[];let maximum=0;for(const value of nums){maximum=Math.max(maximum,value);values.push(gcd(value,maximum));}values.sort((a,b)=>a-b);let answer=0;for(let i=0;i<Math.floor(values.length/2);i++)answer+=gcd(values[i],values[values.length-1-i]);return answer;
}
function gcdSum(nums) { return solve(nums); }
module.exports=solve;
module.exports.gcdSum=gcdSum;
