"use strict";
var input=require("fs").readFileSync("/dev/stdin","utf8");
var cin=input.split(/ |\n/),cid=0;
function next(){return +cin[cid++];}
function nextstr(){return cin[cid++];}
function nextbig(){return BigInt(cin[cid++]);}
function nexts(n,a){return a?cin.slice(cid,cid+=n):cin.slice(cid,cid+=n).map(a=>+a);}
function nextm(h,w,a){var r=[],i=0;if(a)for(;i<h;i++)r.push(cin.slice(cid,cid+=w));else for(;i<h;i++)r.push(cin.slice(cid,cid+=w).map(a=>+a));return r;}
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill().map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill().map(x=>"+r+")";return eval(r);}

var mod = 998244353;
function mul(){for(var a=arguments,r=a[0],i=a.length;--i;)r=((r>>16)*a[i]%mod*65536+(r&65535)*a[i])%mod;return r;}
var fac=[],finv=[],invs=[],pow2=[];
function fset(n){
  fac.length=n+1,fac[0]=fac[1]=1;
  for(var i=2;i<=n;)fac[i]=mul(fac[i-1],i++);
  finv.length=n+1,finv[0]=finv[1]=1,finv[n]=inv(fac[n]);
  for(i=n;2<i;)finv[i-1]=mul(finv[i],i--);
  //invs.length=n+1,invs[0]=invs[1]=1;
  //for(i=2;i<=n;)invs[i]=mul(fac[i-1],finv[i++]);
  //pow2.length=n+1,pow2[0]=1;
  //for(i=1;i<=n;i++)pow2[i]=pow2[i-1]*2%mod;
}
function inv(b){for(var a=mod,u=0,v=1,t;b;v=t)t=a/b|0,a-=t*b,u-=t*v,t=a,a=b,b=t,t=u,u=v;u%=mod;return u<0?u+mod:u;}
function pow(a,n){for(var r=1;n;a=mul(a,a),n>>=1)if(n&1)r=mul(a,r);return r;}
function ncr(n,r){return mul(fac[n],finv[r],finv[n-r]);}
function npr(n,r){return mul(fac[n],finv[n-r]);}
function mput(n){return (n%mod+mod)%mod;}

var myOut = main();
if(myOut !== undefined)console.log(myOut);

function main(){
  var s = nextstr(), sl = s.length;
  var k = next();
  var a = [], x = 0, one = 0;
  for(var i = 0; i < sl; i++){
    if(s[i] === "1")x++, one++;
    else{
      a.push(x);
      x = 0;
    };
  }
  if(x)a.push(x);
  if(a[0])one -= a[0], a[0] = 0;
  k = Math.min(one, k);
  var dp = xArray(0, k+1, k+1);
  dp[0][0] = 1;
  var mn = 0;
  for(var i = 0; i < a.length; i++){
    mn += a[i];
    var dp2 = xArray(0, k+1, k+1);
    for(var k1 = 0; k1 <= k; k1++){
      for(var k2 = 0; k2 <= k1; k2++){
        for(var morau = 0; morau <= one-mn && k1+morau <= k; morau++){
          dp2[k1+morau][k2] += dp[k1][k2];
          dp2[k1+morau][k2] %= mod;
        }
        for(var kubaru = 1; kubaru <= a[i] && kubaru+k2 <= k; kubaru++){
          dp2[k1][k2+kubaru] += dp[k1][k2];
          dp2[k1][k2+kubaru] %= mod;
        }
      }
    }
    dp = dp2;
  }
  var ans = 0;
  for(var i = 0; i <= k; i++)ans += dp[i][i];
  return mput(ans);
}