var GET=(function(){function f(s){return new g(s);}function g(s){this._s=s.trim().split("\n");this._y=0;}g.prototype.a=function(f){var s=this._s, y=this._y, r;if(typeof s[y]==="string")s[y]=s[y].split(" ").reverse();r=s[y].pop();if(!s[y].length)this._y++;return f?r:+r;};g.prototype.l=function(f){var s=this._s[this._y++].split(" ");return f?s:s.map(a=>+a);};g.prototype.m=function(n,f){var r=this._s.slice(this._y,this._y+=n).map(a=>a.split(" "));return f?r:r.map(a=>a.map(a=>+a));};g.prototype.r=function(n,f){var r=this._s.slice(this._y,this._y+=n);return f?r:r.map(a=>+a);};return f;})();
var o=GET(require("fs").readFileSync("/dev/stdin","utf8"));
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill(v)";while(--l)r="Array(a["+l+"]).fill(0).map(x=>"+r+")";return eval(r);}
var mod = 1e9+7;

console.log(main());
function main(){
  var n = o.a();
  var s = o.a(1);
  return solve(s,n);
}

function solve(s,n){
  s = "<" + s;
  var dp = Array(n+1).fill(0);
  dp[0] = 1;
  for(var i = 0; i < n; i++){
    if(s[i] === "<")dp = solveH(dp,n-i);
    else dp = solveL(dp,n-i);
  }
  return dp[0];
}

function solveH(dp,n){
  var dp2 = [dp[0]];
  for(var i = 1; i < n; i++){
    dp2[i] = dp[i] + dp2[i-1];
    dp2[i] %= mod;
  }
  return dp2;
}

function solveL(dp,n){
  var dp2 = Array(n);
  dp2[n-1] = dp[n];
  for(var i = n-1; i; i--){
    dp2[i-1] = dp[i] + dp2[i];
    dp2[i-1] %= mod;
  }
  return dp2;
}