var GET=(function(){function f(s){return new g(s);}function g(s){this._s=s.trim().split("\n");this._y=0;}g.prototype.a=function(f){var s=this._s, y=this._y, r;if(typeof s[y]==="string")s[y]=s[y].split(" ").reverse();r=s[y].pop();if(!s[y].length)this._y++;return f?r:+r;};g.prototype.l=function(f){var s=this._s[this._y++].split(" ");return f?s:s.map(a=>+a);};g.prototype.m=function(n,f){var r=this._s.slice(this._y,this._y+=n).map(a=>a.split(" "));return f?r:r.map(a=>a.map(a=>+a));};g.prototype.r=function(n,f){var r=this._s.slice(this._y,this._y+=n);return f?r:r.map(a=>+a);};return f;})();
var o=GET(require("fs").readFileSync("/dev/stdin","utf8"));
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill(0).map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill(0).map(x=>"+r+")";return eval(r);}
var n, x, ncr, p2n, mod = 998244353;
function abmod(){for(var a=arguments,r=a[0],i=1;i<a.length;)r=((r>>16)*a[i]%mod*65536+(r&65535)*a[i++])%mod;return r;}

console.log(main());
function main(){
  n = o.a();
  x = o.a();
  ncr = Array(n+1);
  p2n = Array(n+1);
  ncr[0] = [1];
  p2n[0] = 1;
  for(var i = 1; i <= n; i++){
    ncr[i] = Array(i+1).fill(1);
    p2n[i] = p2n[i-1] * 2 % mod;
    for(var j = 1; j < i; j++){
      ncr[i][j] = (ncr[i-1][j-1] + ncr[i-1][j]) % mod;
    }
  }
  var t = 0, ans = 1;
  if(x & 1)t = 1, ans = p2n[n];
  for(var i = 1; i <= n && i < x; i++){
    if(i * 2 < x)ans += abmod(ncr[n][i], p2n[i]-t);
    else ans += solve(i);
  }
  return ans % mod;
}
function solve(i){
  var ans = 0;
  for(var j = 0; j < x-i; j++){
    ans += abmod(ncr[n][i], ncr[i][j]);
  }
  for(var j = x-i+1; j < i; j += 2){
    ans += abmod(ncr[n][i], ncr[x-j-1][i-j]);
  }
  return ans % mod;
}