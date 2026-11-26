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

var def = 0;
function segTree(n){
  var x = 2; n--;
  while(n)n >>= 1, x <<= 1;
  this.seg = Array(x-1).fill(def);
  this.l = x >> 1;
}
segTree.prototype={
  get:function(x){
    var v = this.seg;
    x += this.l-1;
    var r = def;
    while(x >= 0){
      if(v[x] > r)r = v[x];
      x = x-1>>1;
    }
    return r;
  },
  update:function(l,r,t){//[l,r)
    if(l >= r)return;
    var self = this;
    q(l,r,0,this.l,0);
    function q(l,r,x,y,i){
      if(l === x && r === y){
        if(self.seg[i] < t)self.seg[i] = t;
        return;
      }
      var m = x+y >> 1;
      if(m < r)if(l < m){q(l,m,x,m,i+i+1);q(m,r,m,y,i+1<<1);}
      else q(l,r,m,y,i+1<<1);
      else q(l,r,x,m,i+i+1);
    }
  },
}

var myOut = main();
if(myOut !== undefined)console.log(String(myOut));
if(streams.length)console.log(streams.join("\n"));

function main(){
  var [n,k] = nexts(2);
  var a = nexts(n);
  var seg = new segTree(300001);
  for(var i = 0; i < n; i++){
    var l = Math.max(0,a[i]-k);
    var r = Math.min(300000,a[i]+k);
    var t = seg.get(a[i]);
    seg.update(l,r+1,t+1);
  }
  var ans = 0;
  for(var i = 0; i <= 300000; i++){
    ans = Math.max(ans,seg.get(i));
  }
  return ans;
}