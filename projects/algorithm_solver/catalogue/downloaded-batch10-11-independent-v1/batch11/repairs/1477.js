'use strict';
// Separate O(n) positive-window variant; all input accesses are reads.
function solve(arr,target){
 const n=arr.length,shortest=new Array(n+1).fill(n+1);let answer=n+1,left=0,total=0;
 for(let right=0;right<n;right++){
  total+=arr[right];while(total>target){total-=arr[left];left++;}
  shortest[right+1]=shortest[right];
  if(total===target){const length=right-left+1;answer=Math.min(answer,length+shortest[left]);shortest[right+1]=Math.min(shortest[right+1],length);}
 }
 return answer===n+1?-1:answer;
}
const minSumOfLengths=solve;
class Solution{minSumOfLengths(arr,target){return solve(arr,target);}}
if(typeof module!=='undefined')module.exports={solve,Solution,minSumOfLengths};
