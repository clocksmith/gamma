var GET=(function(){function f(s){return new g(s);}function g(s){this._s=s.trim().split("\n");this._y=0;}g.prototype.a=function(f){var s=this._s, y=this._y, r;if(typeof s[y]==="string")s[y]=s[y].split(" ").reverse();r=s[y].pop();if(!s[y].length)this._y++;return f?r:+r;};g.prototype.l=function(f){var s=this._s[this._y++].split(" ");return f?s:s.map(a=>+a);};g.prototype.m=function(n,f){var r=this._s.slice(this._y,this._y+=n).map(a=>a.split(" "));return f?r:r.map(a=>a.map(a=>+a));};g.prototype.r=function(n,f){var r=this._s.slice(this._y,this._y+=n);return f?r:r.map(a=>+a);};return f;})();
var o=GET(require("fs").readFileSync("/dev/stdin","utf8"));
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill(0).map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill(0).map(x=>"+r+")";return eval(r);}
var mod = 1e9 + 7;
function abmod(){for(var a=arguments,r=a[0],i=1;i<a.length;)r=((r>>16)*a[i]%mod*65536+(r&65535)*a[i++])%mod;return r;}
function powmod(a,n){for(var r=1;n;a=abmod(a,a),n>>=1)if(n&1)r=abmod(a,r);return r;}

console.log(main());
function main(){
  var n = o.a();
  var a = o.l();
  var mx = 0;
  for(var i = 0; i < n; i++)if(mx < a[i])mx = a[i];
  mx = f(mx);
  var dp = xArray(0,mx);
  var dp0 = xArray(1,mx);
  var c = new Map();
  var x = 0, z = 0;
  for(var i = 0; i < n; i++){
    x ^= a[i];
    if(x === 0)dp0[0]++,z++;
    else{
      solve(x);
    }
  }
  if(x !== 0)return dp0[x];
  var ans = powmod(2,dp0[0]-2);
  for(var i = 1; i < mx; i++)ans += dp[i];
  return ans % mod;
  
  function solve(x){
    if(c.has(x) && c.get(x) < z){
      dp0[x] += abmod(z-c.get(x),dp[x]);
      dp0[x] %= mod;
    }
    c.set(x,z);
    dp[x] += dp0[x];
    dp[x] %= mod;
  }
}
function f(a){
  var r=1;
  while(a)r<<=1,a>>=1;
  return r;
}