"use strict";
class MinHeap {
 constructor(compare=(a,b)=>a-b){this.data=[];this.compare=compare;}
 get size(){return this.data.length;}
 peek(){return this.data[0];}
 push(value){const a=this.data;let i=a.length;a.push(value);while(i){const p=(i-1)>>1;if(this.compare(a[p],value)<=0)break;a[i]=a[p];i=p;}a[i]=value;}
 pop(){const a=this.data,result=a[0],last=a.pop();if(a.length){let i=0;while(2*i+1<a.length){let c=2*i+1;if(c+1<a.length&&this.compare(a[c+1],a[c])<0)c++;if(this.compare(last,a[c])<=0)break;a[i]=a[c];i=c;}a[i]=last;}return result;}
}
class DinnerPlates{constructor(capacity){this.capacity=capacity;this.stacks=[];this.available=new MinHeap();this.right=-1;}push(val){if(!this.available.size){this.stacks.push([]);this.available.push(this.stacks.length-1);}const i=this.available.peek();this.stacks[i].push(val);this.right=Math.max(this.right,i);if(this.stacks[i].length===this.capacity)this.available.pop();}pop(){return this.popAtStack(this.right);}popAtStack(index){if(index<0||index>=this.stacks.length||!this.stacks[index].length)return -1;if(this.stacks[index].length===this.capacity)this.available.push(index);const v=this.stacks[index].pop();while(this.right>=0&&!this.stacks[this.right].length)this.right--;return v;}}

function solve(operations,args){const x=new DinnerPlates(...args[0]),out=[null];for(let i=1;i<operations.length;i++){const v=x[operations[i]](...args[i]);out.push(v===undefined?null:v);}return out;}
module.exports=solve;
module.exports.DinnerPlates=DinnerPlates;
