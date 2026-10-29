"use strict";
class MinHeap {
 constructor(compare=(a,b)=>a-b){this.data=[];this.compare=compare;}
 get size(){return this.data.length;}
 peek(){return this.data[0];}
 push(value){const a=this.data;let i=a.length;a.push(value);while(i){const p=(i-1)>>1;if(this.compare(a[p],value)<=0)break;a[i]=a[p];i=p;}a[i]=value;}
 pop(){const a=this.data,result=a[0],last=a.pop();if(a.length){let i=0;while(2*i+1<a.length){let c=2*i+1;if(c+1<a.length&&this.compare(a[c+1],a[c])<0)c++;if(this.compare(last,a[c])<=0)break;a[i]=a[c];i=c;}a[i]=last;}return result;}
}
const compareEntries=(a,b)=>{for(let i=0;i<a.length;i++)if(a[i]!==b[i])return a[i]-b[i];return 0;};class MovieRentingSystem{constructor(n,entries){this.records=new Map();this.available=new Map();this.rented=new MinHeap(compareEntries);for(const [shop,movie,price]of entries){this.records.set(shop+','+movie,{price,version:0,rented:false});if(!this.available.has(movie))this.available.set(movie,new MinHeap(compareEntries));this.available.get(movie).push([price,shop,0]);}}search(movie){const heap=this.available.get(movie);if(!heap)return [];const kept=[];while(heap.size&&kept.length<5){const e=heap.pop(),r=this.records.get(e[1]+','+movie);if(!r.rented&&r.version===e[2])kept.push(e);}for(const e of kept)heap.push(e);return kept.map(e=>e[1]);}rent(shop,movie){const r=this.records.get(shop+','+movie);r.version++;r.rented=true;this.rented.push([r.price,shop,movie,r.version]);}drop(shop,movie){const r=this.records.get(shop+','+movie);r.version++;r.rented=false;this.available.get(movie).push([r.price,shop,r.version]);}report(){const kept=[];while(this.rented.size&&kept.length<5){const e=this.rented.pop(),r=this.records.get(e[1]+','+e[2]);if(r.rented&&r.version===e[3])kept.push(e);}for(const e of kept)this.rented.push(e);return kept.map(e=>[e[1],e[2]]);}}

function solve(operations,args){const x=new MovieRentingSystem(...args[0]),out=[null];for(let i=1;i<operations.length;i++){const v=x[operations[i]](...args[i]);out.push(v===undefined?null:v);}return out;}
module.exports=solve;
module.exports.MovieRentingSystem=MovieRentingSystem;
