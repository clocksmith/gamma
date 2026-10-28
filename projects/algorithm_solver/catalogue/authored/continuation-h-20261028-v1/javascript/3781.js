"use strict";
function solve(nums, s) {
const heap=[];function push(value){let i=heap.length;heap.push(value);while(i){const parent=Math.floor((i-1)/2);if(heap[parent]>=value)break;heap[i]=heap[parent];i=parent;}heap[i]=value;}function pop(){const result=heap[0],last=heap.pop();if(heap.length){let i=0;while(i*2+1<heap.length){let child=i*2+1;if(child+1<heap.length&&heap[child+1]>heap[child])child++;if(heap[child]<=last)break;heap[i]=heap[child];i=child;}heap[i]=last;}return result;}let answer=0;for(let i=0;i<nums.length;i++){push(nums[i]);if(s[i]==='1')answer+=pop();}return answer;
}
function maximumScore(nums, s) { return solve(nums, s); }
module.exports=solve;
module.exports.maximumScore=maximumScore;
