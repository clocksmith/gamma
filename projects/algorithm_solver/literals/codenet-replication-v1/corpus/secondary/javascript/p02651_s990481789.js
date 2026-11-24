"use strict";
var input=require("fs").readFileSync("/dev/stdin","utf8");
var cin=input.split(/ |\n/),cid=0;
function next(){return +cin[cid++];}
function nextstr(){return cin[cid++];}
function nextbig(){return BigInt(cin[cid++]);}
function nexts(n,a){return a?cin.slice(cid,cid+=n):cin.slice(cid,cid+=n).map(a=>+a);}
function nextm(h,w,a){var r=[],i=0;if(a)for(;i<h;i++)r.push(cin.slice(cid,cid+=w));else for(;i<h;i++)r.push(cin.slice(cid,cid+=w).map(a=>+a));return r;}
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill().map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill().map(x=>"+r+")";return eval(r);}

class solve{
  constructor(){
    this.a = Array(60).fill(0n);
  }
  add(s){
    var c = 0, t = BigInt(s);
    for(var i = 60; i--;){
      if((t >> BigInt(i)) & 1n){
        if(this.a[i])t ^= this.a[i];
        else c = Math.max(i,c);
      }
    }
    if(t)this.a[c] = t;
  }
  has(s){
    var t = BigInt(s);
    for(var i = 60; i--;){
      if((t >> BigInt(i)) & 1n){
        if(this.a[i])t ^= this.a[i];
        else return false;
      }
    }
    return true;
  }
}

var myOut = main();
if(myOut !== undefined)console.log(String(myOut));

function main(){
  var t = next();
  for(var i = 0; i < t; i++){
    var n = next();
    var a = nexts(n,1);
    var s = nextstr();
    var flag = 0;
    var f = new solve();
    for(var j = n; j--;){
      if(s[j] === "0")f.add(a[j]);
      else{
        if(!f.has(a[j])){
          flag = 1;
          break;
        }
      }
    }
    console.log(flag);
  }
}