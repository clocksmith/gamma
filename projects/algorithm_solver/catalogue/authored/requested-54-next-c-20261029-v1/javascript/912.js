"use strict";
function solve(nums){const a=nums.slice();function sift(root,end){while(2*root+1<end){let child=2*root+1;if(child+1<end&&a[child]<a[child+1])child++;if(a[root]>=a[child])return;[a[root],a[child]]=[a[child],a[root]];root=child;}}
 for(let i=Math.floor(a.length/2)-1;i>=0;i--)sift(i,a.length);for(let end=a.length-1;end>0;end--){[a[0],a[end]]=[a[end],a[0]];sift(0,end);}return a;
}

function sortArray(nums) { return solve(nums); }
module.exports=solve;module.exports.sortArray=sortArray;
