"use strict";
var GET=(function(){function f(s){return new g(s);}function g(s){this._s=s.trim().split("\n");this._y=0;}g.prototype.a=function(f){var s=this._s, y=this._y, r;if(typeof s[y]==="string")s[y]=s[y].split(" ").reverse();r=s[y].pop();if(!s[y].length)this._y++;return f?r:+r;};g.prototype.l=function(f){var s=this._s[this._y++].split(" ");return f?s:s.map(a=>+a);};g.prototype.m=function(n,f){var r=this._s.slice(this._y,this._y+=n).map(a=>a.split(" "));return f?r:r.map(a=>a.map(a=>+a));};g.prototype.r=function(n,f){var r=this._s.slice(this._y,this._y+=n);return f?r:r.map(a=>+a);};return f;})();
var o=GET(require("fs").readFileSync("/dev/stdin","utf8"));
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill(0).map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill(0).map(x=>"+r+")";return eval(r);}
var mod = 1e9+7;
function mul(){for(var a=arguments,r=a[0],i=a.length;--i;)r=((r>>16)*a[i]%mod*65536+(r&65535)*a[i])%mod;return r;}
var fac=[],finv=[],invs=[],pow2=[];
function fset(n){
  fac.length=n+1,fac[0]=fac[1]=1;
  for(var i=2;i<=n;)fac[i]=mul(fac[i-1],i++);
  finv.length=n+1,finv[0]=finv[1]=1,finv[n]=inv(fac[n]);
  for(i=n;2<i;)finv[i-1]=mul(finv[i],i--);
  invs.length=n+1,invs[0]=invs[1]=1;
  for(i=2;i<=n;)invs[i]=mul(fac[i-1],finv[i++]);
  pow2.length=n+1,pow2[0]=1;
  for(i=1;i<=n;i++)pow2[i]=pow2[i-1]*2%mod;
}
function inv(b){for(var a=mod,u=0,v=1,t;b;v=t)t=a/b|0,a-=t*b,u-=t*v,t=a,a=b,b=t,t=u,u=v;u%=mod;return u<0?u+mod:u;}
function pow(a,n){for(var r=1;n;a=mul(a,a),n>>=1)if(n&1)r=mul(a,r);return r;}
function ncr(n,r){return mul(fac[n],finv[r],finv[n-r]);}
function npr(n,r){return mul(fac[n],finv[r]);}

console.log(main());
function main(){
  var n = o.a();
  var x = o.l();
  fset(n+1);
  var ans = 0;
  var u = fac[n-1];
  for(var i = 1; i < n; i++){
    ans += mul(x[i]-x[i-1],u);
    u = (u+mul(fac[n-1],invs[i+1]))%mod;
  }
  return ans%mod;
}