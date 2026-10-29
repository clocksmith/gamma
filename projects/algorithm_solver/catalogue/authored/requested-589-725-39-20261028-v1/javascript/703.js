"use strict";
class MinHeap {
 constructor(compare=(a,b)=>a-b){this.data=[];this.compare=compare;}
 get size(){return this.data.length;}
 peek(){return this.data[0];}
 push(value){const a=this.data;let i=a.length;a.push(value);while(i){const p=(i-1)>>1;if(this.compare(a[p],value)<=0)break;a[i]=a[p];i=p;}a[i]=value;}
 pop(){const a=this.data,result=a[0],last=a.pop();if(a.length){let i=0;while(2*i+1<a.length){let c=2*i+1;if(c+1<a.length&&this.compare(a[c+1],a[c])<0)c++;if(this.compare(last,a[c])<=0)break;a[i]=a[c];i=c;}a[i]=last;}return result;}
}
class KthLargest{constructor(k,nums){this.k=k;this.heap=new MinHeap();for(const value of nums){this.heap.push(value);if(this.heap.size>k)this.heap.pop();}}add(val){if(this.heap.size<this.k)this.heap.push(val);else if(val>this.heap.peek()){this.heap.pop();this.heap.push(val);}return this.heap.peek();}}

function solve(operations,args){const instance=new KthLargest(...args[0]),out=[null];for(let i=1;i<operations.length;i++){const result=instance[operations[i]](...args[i]);out.push(result===undefined?null:result);}return out;}
module.exports=solve;
module.exports.KthLargest=KthLargest;
