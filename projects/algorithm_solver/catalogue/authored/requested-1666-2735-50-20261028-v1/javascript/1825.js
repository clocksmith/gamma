"use strict";
class MKAverage{constructor(m,k){this.m=m;this.k=k;this.queue=new Array(m);this.head=0;this.size=0;this.count=new Int32Array(100001);this.sums=new Float64Array(100001);}update(value,delta){for(let i=value;i<=100000;i+=i&-i){this.count[i]+=delta;this.sums[i]+=value*delta;}}addElement(num){if(this.size===this.m){this.update(this.queue[this.head],-1);this.queue[this.head]=num;this.head=(this.head+1)%this.m;}else{this.queue[(this.head+this.size)%this.m]=num;this.size++;}this.update(num,1);}first(k){let i=0,count=0,total=0;for(let bit=65536;bit;bit=Math.floor(bit/2)){const j=i+bit;if(j<=100000&&count+this.count[j]<=k){i=j;count+=this.count[j];total+=this.sums[j];}}return total+(k-count)*(i+1);}calculateMKAverage(){if(this.size<this.m)return -1;return Math.floor((this.first(this.m-this.k)-this.first(this.k))/(this.m-2*this.k));}}

function solve(operations,args){const x=new MKAverage(...args[0]),out=[null];for(let i=1;i<operations.length;i++){const v=x[operations[i]](...args[i]);out.push(v===undefined?null:v);}return out;}
module.exports=solve;
module.exports.MKAverage=MKAverage;
