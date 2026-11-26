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
  var n = next(), k = next();
  var a = [];
  for(var i = 0; i < n; i++){
    var t = next();
    if(t < k)a.push(t);
  }
  n = a.length;
  a.sort((a,b)=>b-a);
  var dp = xArray(0,k);
  dp[0] = 1;
  var q = -1;
  for(var i = 0; i < n; i++){
    var t = a[i];
    for(var j = k-t; j < k; j++){
      if(dp[j]){
        q = i;
        break;
      }
    }
    for(var j = k-t; j--;){
      dp[j+t] |= dp[j];
    }
  }
  return n-q-1;
}