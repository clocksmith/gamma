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
  var n = next();
  var a = next(1);
  var b = Array(n-1);
  var n2 = n-1, x = [0,0,0];
  for(var i = 0; i < n2; i++){
    var y = Math.abs(a[i]-a[i+1]);
    b[i] = y;
    x[y]++;
  }
  var z = solve(b)[0];
  if(x[1] && z === 2)return 0;
  return z;
}

function solve(b){
  var bl = b.length;
  if(bl === 1)return b;
  var c = [], d = 1 << 31-Math.clz32(bl), s = 0;
  for(var i = 0; i < d; i++){
    s ^= b[i];
  }
  for(i--;;){
    var t = s === 3 ? 1 : s;
    c.push(t);
    i++;
    if(i === bl)break;
    s ^= b[i];
    s ^= b[i-d]
  }
  return solve(c);
}