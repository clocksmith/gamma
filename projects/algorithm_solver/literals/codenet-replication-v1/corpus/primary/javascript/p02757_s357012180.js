"use strict";
var input=require("fs").readFileSync("/dev/stdin","utf8");
var cin=input.split(/ |\n/),cid=0;
function next(a){return a?cin[cid++]:+cin[cid++];}
function nexts(n,a){return a?cin.slice(cid,cid+=n):cin.slice(cid,cid+=n).map(a=>+a);}
function nextm(h,w,a){var r=[],i=0;if(a)for(;i<h;i++)r.push(cin.slice(cid,cid+=w));else for(;i<h;i++)r.push(cin.slice(cid,cid+=w).map(a=>+a));return r;}
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill().map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill().map(x=>"+r+")";return eval(r);}

var myOut = main();
if(myOut !== undefined)console.log(myOut);

function main(){
  var n = next(), p = next();
  var s = next(1);
  var ans = 0;
  if(10 % p === 0){
    for(var i = 0; i < n; i++){
      if(s[i] % p === 0)ans += i+1;
    }
    return ans;
  }
  var map = xArray(0,p);
  map[0] = 1;
  var keta = 1, val = 0;
  for(var i = n; i--;){
    val += s[i] * keta;
    val %= p;
    map[val]++;
    keta *= 10;
    keta %= p;
  }
  for(var i = 0; i < p; i++)ans += map[i]*(map[i]-1)/2;
  return ans;
}