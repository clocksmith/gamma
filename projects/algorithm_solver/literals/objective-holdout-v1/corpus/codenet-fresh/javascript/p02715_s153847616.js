"use strict";
var input=require("fs").readFileSync("/dev/stdin","utf8");
var cin=input.split(/ |\n/),cid=0;
function next(a){return a?cin[cid++]:+cin[cid++];}
function nexts(n,a){return a?cin.slice(cid,cid+=n):cin.slice(cid,cid+=n).map(a=>+a);}
function nextm(h,w,a){var r=[],i=0;if(a)for(;i<h;i++)r.push(cin.slice(cid,cid+=w));else for(;i<h;i++)r.push(cin.slice(cid,cid+=w).map(a=>+a));return r;}
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill().map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill().map(x=>"+r+")";return eval(r);}

var mod = 1e9+7;
function mul(){for(var a=arguments,r=a[0],i=a.length;--i;)r=((r>>16)*a[i]%mod*65536+(r&65535)*a[i])%mod;return r;}
function pow(a,n){for(var r=1;n;a=mul(a,a),n>>=1)if(n&1)r=mul(a,r);return r;}

var myOut = main();
if(myOut !== undefined)console.log(myOut);

function main(){
  var n = next();
  var k = next();
  var s = xArray(0,k+1);
  var ans = k;
  s[k] = 1;
  for(var i = k-1; i > 0; i--){
    s[i] = pow(k/i|0, n);
    for(var j = i+i; j <= k; j += i){
      s[i] -= s[j];
    }
    s[i] %= mod;
    if(s[i] < 0)s[i] += mod;
    ans += mul(s[i], i);
 }
  return ans % mod;
}