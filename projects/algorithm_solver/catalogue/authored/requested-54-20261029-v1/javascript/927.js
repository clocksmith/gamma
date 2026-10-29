"use strict";
function solve(arr){const ones=[];for(let i=0;i<arr.length;i++)if(arr[i])ones.push(i);if(!ones.length)return [0,2];if(ones.length%3)return [-1,-1];
 const g=ones.length/3,a=ones[0],b=ones[g],c=ones[2*g],size=arr.length-c;if(a+size>b||b+size>c)return [-1,-1];
 for(let i=0;i<size;i++)if(arr[a+i]!==arr[b+i]||arr[a+i]!==arr[c+i])return [-1,-1];return [a+size-1,b+size];
}

function threeEqualParts(arr) { return solve(arr); }
module.exports=solve;
module.exports.threeEqualParts=threeEqualParts;
