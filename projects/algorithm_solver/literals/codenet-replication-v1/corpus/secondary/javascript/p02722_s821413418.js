"use strict";
var input=require("fs").readFileSync("/dev/stdin","utf8");
var cin=input.split(/ |\n/),cid=0;
function next(a){return a?cin[cid++]:+cin[cid++];}
function nexts(n,a){return a?cin.slice(cid,cid+=n):cin.slice(cid,cid+=n).map(a=>+a);}
function nextm(h,w,a){var r=[],i=0;if(a)for(;i<h;i++)r.push(cin.slice(cid,cid+=w));else for(;i<h;i++)r.push(cin.slice(cid,cid+=w).map(a=>+a));return r;}
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill().map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill().map(x=>"+r+")";return eval(r);}

var set = new Set();
var myOut = main();
if(myOut !== undefined)console.log(myOut);

function main(){
  var n = next();
  var ans = 0;
  for(var i = 0; i < 2; i++){
    var d = solve(n - i);
    for(var j = 0; j < d.length; j++){
      var t = d[j], m = n;
      while(m % t === 0)m /= t;
      if(m % t === 1)
        ans++;
    }
  }
  return ans;
}

function solve(x){
  if(x === 1)return [];
  var r = [x];
  for(var i = 2; i*i <= x; i++){
    if(x % i === 0){
      if(!set.has(i))set.add(i), r.push(i);
      if(!set.has(x/i))set.add(x/i), r.push(x/i);
    }
  }
  return r;
}