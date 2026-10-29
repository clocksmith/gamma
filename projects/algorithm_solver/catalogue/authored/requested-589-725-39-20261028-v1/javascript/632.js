"use strict";
class MinHeap {
 constructor(compare=(a,b)=>a-b){this.data=[];this.compare=compare;}
 get size(){return this.data.length;}
 peek(){return this.data[0];}
 push(value){const a=this.data;let i=a.length;a.push(value);while(i){const p=(i-1)>>1;if(this.compare(a[p],value)<=0)break;a[i]=a[p];i=p;}a[i]=value;}
 pop(){const a=this.data,result=a[0],last=a.pop();if(a.length){let i=0;while(2*i+1<a.length){let c=2*i+1;if(c+1<a.length&&this.compare(a[c+1],a[c])<0)c++;if(this.compare(last,a[c])<=0)break;a[i]=a[c];i=c;}a[i]=last;}return result;}
}
function solve(nums){const heap=new MinHeap((a,b)=>a[0]-b[0]||a[1]-b[1]);let high=-Infinity;for(let i=0;i<nums.length;i++){heap.push([nums[i][0],i,0]);high=Math.max(high,nums[i][0]);}let best=[heap.peek()[0],high];while(true){const [low,row,col]=heap.pop();if(high-low<best[1]-best[0]||(high-low===best[1]-best[0]&&low<best[0]))best=[low,high];if(col+1===nums[row].length)return best;const value=nums[row][col+1];high=Math.max(high,value);heap.push([value,row,col+1]);}}

function smallestRange(nums){return solve(nums);}
module.exports=solve;
module.exports.smallestRange=smallestRange;
