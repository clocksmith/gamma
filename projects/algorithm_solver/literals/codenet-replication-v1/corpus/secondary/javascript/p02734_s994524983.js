"use strict";
var input=require("fs").readFileSync("/dev/stdin","utf8");
var cin=input.split(/ |\n/),cid=0;
function next(a){return a?cin[cid++]:+cin[cid++];}
function nexts(n,a){return a?cin.slice(cid,cid+=n):cin.slice(cid,cid+=n).map(a=>+a);}
function nextm(h,w,a){var r=[],i=0;if(a)for(;i<h;i++)r.push(cin.slice(cid,cid+=w));else for(;i<h;i++)r.push(cin.slice(cid,cid+=w).map(a=>+a));return r;}
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill().map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill().map(x=>"+r+")";return eval(r);}

var mod = 998244353;
function mul(){for(var a=arguments,r=a[0],i=a.length;--i;)r=((r>>16)*a[i]%mod*65536+(r&65535)*a[i])%mod;return r;}
var myOut = main();
if(myOut !== undefined)console.log(myOut);

function main(){
  var n = next(), s = next();
  var a = nexts(n);
  var dp = xArray(0,s);
  var ans = 0;
  for(var i = 0; i < n; i++){
    var t = a[i], l = i+1, r = n-i;
    if(t === s)ans += mul(l,r);
    if(t >= s)continue;
    ans += mul(dp[s-t],r);
    for(var j = s-t; --j;){
      dp[j+t] += dp[j];
      dp[j+t] %= mod;
    }
    dp[t] += l;
    dp[t] %= mod;
  }
  return ans % mod;
}