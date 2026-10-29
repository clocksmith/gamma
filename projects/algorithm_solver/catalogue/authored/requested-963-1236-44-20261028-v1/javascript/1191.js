"use strict";
function solve(arr,k){const total=arr.reduce((a,b)=>a+b,0);let best=0,current=0;for(let i=0;i<arr.length*Math.min(k,2);i++){current=Math.max(0,current+arr[i%arr.length]);best=Math.max(best,current);}return (best+Math.max(0,total)*Math.max(0,k-2))%1000000007;}

function kConcatenationMaxSum(arr, k){return solve(arr, k);}
module.exports=solve;
module.exports.kConcatenationMaxSum=kConcatenationMaxSum;
