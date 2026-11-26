"use strict";
var input=require("fs").readFileSync("/dev/stdin","utf8");
var cin=input.split(/ |\n/),cid=0;
function next(){return +cin[cid++];}
function nextstr(){return cin[cid++];}
function nextbig(){return BigInt(cin[cid++]);}
function nexts(n,a){return a?cin.slice(cid,cid+=n):cin.slice(cid,cid+=n).map(a=>+a);}
function nextssort(n,a){return a?cin.slice(cid,cid+=n).map(a=>+a).sort((a,b)=>b-a):cin.slice(cid,cid+=n).map(a=>+a).sort((a,b)=>a-b);}
function nextm(h,w,a){var r=[],i=0;if(a)for(;i<h;i++)r.push(cin.slice(cid,cid+=w));else for(;i<h;i++)r.push(cin.slice(cid,cid+=w).map(a=>+a));return r;}
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill().map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill().map(x=>"+r+")";return eval(r);}
var streams=[];function print(s){streams.push(s);}

class unionFind{
  constructor(n){this.a=Array(n+1).fill(-1);}
  root(i){
    return this.a[i]<0?i:this.a[i]=this.root(this.a[i]);
  }
  same(x,y){return this.root(x)===this.root(y);}
  unite(x,y){
    const a=this.a;
    x=this.root(x),y=this.root(y);
    if(x===y)return false;
    if(a[y]<a[x])a[y]+=a[x],a[x]=y;
    else a[x]+=a[y],a[y]=x;
    return true;
  }
  size(i){return -this.a[this.root(i)];}
}

class priorityQueue{
  constructor(){
    this.a=[];
  }
  push(num,inc){
    const a = this.a;
    for(var i = a.length, j; i; i = j){
      j = i - 1 >> 1;
      if(a[j][0] <= num)break;
      a[i] = a[j];
    }
    a[i] = [num,inc];
  }
  pop(){
    const a = this.a, r = a[0], x = a.pop(), k = a.length >> 1;
    for(var i = 0, j; i < k; i = j){
      j = (i << 1) + 1;
      if(a[j+1] && a[j+1][0] < a[j][0])j++;
      if(x[0] <= a[j][0])break;
      a[i] = a[j];
    }
    if(a.length)a[i] = x;
    return r;
  }
  get size(){
    return this.a.length;
  }
  get top(){
    return this.a[0];
  }
}

var myOut = main();
if(myOut !== undefined)console.log(String(myOut));
if(streams.length)console.log(streams.join("\n"));

function main(){
  var n = next();
  var z = [];
  for(var i = 0; i < n; i++){
    z.push([next(),next(),i]);
  }
  z.sort((a,b)=>a[0]-b[0]);
  var uf = new unionFind(n+1);
  var pq = new priorityQueue();
  for(var i = 0; i < n; i++){
    var [x,y,id] = z[i];
    var y2 = y, id2 = id;
    while(pq.size && pq.top[0] < y){
      var [y3,id3] = pq.pop();
      uf.unite(id,id3);
      if(y3 < y2)y2 = y3, id2 = id3;
    }
    pq.push(y2,id2);
  }
  for(var i = 0; i < n; i++){
    print(uf.size(i));
  }
}