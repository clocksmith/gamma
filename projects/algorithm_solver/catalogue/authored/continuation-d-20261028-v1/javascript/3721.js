"use strict";
// Original development candidate; qualification pending.
function solve(nums) {
const n=nums.length,low=new Int32Array(4*n),high=new Int32Array(4*n),lazy=new Int32Array(4*n);
function apply(node,value){low[node]+=value;high[node]+=value;lazy[node]+=value;}
function push(node){if(lazy[node]){apply(node*2,lazy[node]);apply(node*2+1,lazy[node]);lazy[node]=0;}}
function add(node,left,right,start,end,value){if(start<=left&&right<=end){apply(node,value);return;}push(node);const middle=Math.floor((left+right)/2);if(start<=middle)add(node*2,left,middle,start,end,value);if(end>middle)add(node*2+1,middle+1,right,start,end,value);low[node]=Math.min(low[node*2],low[node*2+1]);high[node]=Math.max(high[node*2],high[node*2+1]);}
function firstZero(node,left,right,bound){if(left>bound||low[node]>0||high[node]<0)return -1;if(left===right)return left;push(node);const middle=Math.floor((left+right)/2),found=firstZero(node*2,left,middle,bound);return found!==-1?found:firstZero(node*2+1,middle+1,right,bound);}
const last=new Map();let best=0;for(let right=0;right<n;right++){const value=nums[right];add(1,0,n-1,(last.has(value)?last.get(value):-1)+1,right,value%2===0?1:-1);last.set(value,right);const left=firstZero(1,0,n-1,right);if(left!==-1)best=Math.max(best,right-left+1);}return best;
}
function longestBalanced(nums) { return solve(nums); }
module.exports = solve;
module.exports.longestBalanced = longestBalanced;
