"use strict";
var input=require("fs").readFileSync("/dev/stdin","utf8");
var cin=input.split(/ |\n/),cid=0;
function next(){return +cin[cid++];}
function nextstr(){return cin[cid++];}
function nextbig(){return BigInt(cin[cid++]);}
function nexts(n,a){return a?cin.slice(cid,cid+=n):cin.slice(cid,cid+=n).map(a=>+a);}
function nextm(h,w,a){var r=[],i=0;if(a)for(;i<h;i++)r.push(cin.slice(cid,cid+=w));else for(;i<h;i++)r.push(cin.slice(cid,cid+=w).map(a=>+a));return r;}
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill().map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill().map(x=>"+r+")";return eval(r);}
function lowerBound(ary,v,l,r){--l;for(var c;1<r-l;)ary[c=l+r>>1]<v?l=c:r=c;return r;}

var myOut = main();
if(myOut !== undefined)console.log(String(myOut));

function main(){
  var s = nextstr();
  var n = s.length;
  var map = new Map();
  var x = 0;
  for(var i = 0; i < n; i++){
    x ^= 1 << (s[i].charCodeAt()-97);
    if(map.has(x))map.get(x).push(i+1);
    else map.set(x,[i+1]);
  }
  var dp = xArray(1e9,n+1);
  dp[0] = 0, x = 0;
  var map2 = new Map();
  for(var i = 0; i < n; i++){
    if(map2.has(x)){
      if(map2.get(x) > dp[i])map2.set(x,dp[i]);
    }else map2.set(x,dp[i]);
    x ^= 1 << (s[i].charCodeAt()-97);
    solve(x,i+1);
    for(var j = 0; j < 26; j++){
      solve(x ^ (1 << j),i+1);
    }
  }
  return dp[n];

  function solve(bit,i){
    if(map2.has(bit)){
      if(map2.get(bit) + 1 < dp[i])
      dp[i] = map2.get(bit) + 1;
    }
  }
}