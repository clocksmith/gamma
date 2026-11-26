"use strict";
var input=require("fs").readFileSync("/dev/stdin","utf8");
var cin=input.split(/ |\n/),cid=0;
function next(){return +cin[cid++];}
function nextstr(){return cin[cid++];}
function nextbig(){return BigInt(cin[cid++]);}
function nexts(n,a){return a?cin.slice(cid,cid+=n):cin.slice(cid,cid+=n).map(a=>+a);}
function nextm(h,w,a){var r=[],i=0;if(a)for(;i<h;i++)r.push(cin.slice(cid,cid+=w));else for(;i<h;i++)r.push(cin.slice(cid,cid+=w).map(a=>+a));return r;}
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill().map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill().map(x=>"+r+")";return eval(r);}

var myOut = main();
if(myOut !== undefined)console.log(String(myOut));

function main(){
  var s = nextstr().split("");
  var n = s.length;
  var mx = 0;
  var dp = Array(n+1);
  dp[0] = 0;
  for(var i = 0; i < n; i++){
    dp[i+1] = dp[i] + (s[i] === "1" ? 1 : -1);
    if(mx < dp[i+1])mx = dp[i+1];
  }
  for(var i = n; i--; i){
    dp[i] = Math.max(dp[i], dp[i+1]);
  }
  var mn = [0,0], p = [0,0];
  for(var j = 0, x=0; j < 2; j++,x=0)for(var i = 0; i < n; i++){
    if(s[i] === "?"){
      if(p[j]+dp[i+1]+2 <= mx+j)p[j] += 2, x++;
      else x--;
    }else if(s[i] === "1")x++; else x--;
    if(x < mn[j])mn[j] = x;
  }
  return Math.min(mx-mn[0], mx+1-mn[1]);
}