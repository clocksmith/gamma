var GET=(function(){function f(s){return new g(s);}function g(s){this._s=s.trim().split("\n");this._y=0;}g.prototype.a=function(f){var s=this._s, y=this._y, r;if(typeof s[y]==="string")s[y]=s[y].split(" ").reverse();r=s[y].pop();if(!s[y].length)this._y++;return f?r:+r;};g.prototype.l=function(f){var s=this._s[this._y++].split(" ");return f?s:s.map(a=>+a);};g.prototype.m=function(n,f){var r=this._s.slice(this._y,this._y+=n).map(a=>a.split(" "));return f?r:r.map(a=>a.map(a=>+a));};g.prototype.r=function(n,f){var r=this._s.slice(this._y,this._y+=n);return f?r:r.map(a=>+a);};return f;})();
var o=GET(require("fs").readFileSync("/dev/stdin","utf8"));
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill(v)";while(--l)r="Array(a["+l+"]).fill(0).map(x=>"+r+")";return eval(r);}
var mod = 1e9 + 7;
var fact=[1,1];
var finv=[1,1];
function abmod(){for(var a=arguments,r=a[0],i=1;i<a.length;)r=((r>>16)*a[i]%mod*65536+(r&65535)*a[i++])%mod;return r;}
function modinv(a){for(var b=mod,u=1,v=0,t;b;v=t)t=a/b|0,a-=t*b,u-=t*v,t=a,a=b,b=t,t=u,u=v;u%=mod;return u<0?u+mod:u;}
function nCrmod(n,r){return abmod(fact[n],finv[r],finv[n-r]);}

console.log(main());
function main(){
  var B = o.a();
  var W = o.a();
  var s = B+W;
  fact.length = finv.length = s+1;
  for(var i = 2; i <= s; i++)fact[i] = abmod(fact[i-1], i);
  finv[s] = modinv(fact[s]);
  for(var i = s; i > 2; i--)finv[i-1] = abmod(finv[i], i);
  var ans = Array(s);
  var m = 1, b = 0, w = 0;
  for(var i = 0; i < s; i++){
    if(B <= i){
      if(B === i)b = 1;
      else b *= 2, b += nCrmod(i-1,B-1), b %= mod;
    }
    if(W <= i){
      if(W === i)w = 1;
      else w *= 2, w += nCrmod(i-1,W-1), w %= mod;
    }
    ans[i] = w;
    var t = m - w - b;
    while(t < 0)t += mod;
    ans[i] += abmod(finv[2], t);
    ans[i] = abmod(ans[i],modinv(m));
    m = m * 2 % mod;
  }
  return ans.join("\n");
}