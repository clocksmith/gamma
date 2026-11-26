var GET=(function(){function f(s){return new g(s);}function g(s){this._s=s.trim().split("\n");this._y=0;}g.prototype.a=function(f){var s=this._s, y=this._y, r;if(typeof s[y]==="string")s[y]=s[y].split(" ").reverse();r=s[y].pop();if(!s[y].length)this._y++;return f?r:+r;};g.prototype.l=function(f){var s=this._s[this._y++].split(" ");return f?s:s.map(a=>+a);};g.prototype.m=function(n,f){var r=this._s.slice(this._y,this._y+=n).map(a=>a.split(" "));return f?r:r.map(a=>a.map(a=>+a));};g.prototype.r=function(n,f){var r=this._s.slice(this._y,this._y+=n);return f?r:r.map(a=>+a);};return f;})();
var o=GET(require("fs").readFileSync("/dev/stdin","utf8"));
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill(0).map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill(0).map(x=>"+r+")";return eval(r);}
var mod = 1e9 + 7;
function abmod(){for(var a=arguments,r=a[0],i=1;i<a.length;)r=((r>>16)*a[i]%mod*65536+(r&65535)*a[i++])%mod;return r;}
var fact=[1,1];
function factmod(n){for(var i=fact.length;i<=n;i++)fact[i]=abmod(fact[i-1],i);return fact[n];}
function nCrmod(n,r){return abmod(factmod(n),modinv(factmod(r)),modinv(factmod(n-r)));}
function modinv(a){for(var b=mod,u=1,v=0,t;b;v=t)t=a/b|0,a-=t*b,u-=t*v,t=a,a=b,b=t,t=u,u=v;u%=mod;return u<0?u+mod:u;}

console.log(main());
function main(){
  var n = o.a();
  var m = o.a();
  var k = o.a();
  var a = xArray(0,n,m);
  for(var x = 0; x < m; x++){
    for(var y = 0; y < n; y++){
      a[y][x] = (f(x+1) + f(m-x)) * n;
      a[y][x] += (f(y+1) + f(n-y)) * m;
    }
  }
  var ans = 0;
  for(var x = 0; x < m; x++){
    for(var y = 0; y < n; y++){
      ans += a[y][x];
    }
  }
  ans %= mod;
  return abmod(ans,nCrmod(n*m-2,k-2),modinv(2));
}
function f(a){
  return a*(a-1)/2;
}