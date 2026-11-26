var GET=(function(){function f(s){return new g(s);}function g(s){this._s=s.trim().split("\n");this._y=0;}g.prototype.a=function(f){var s=this._s, y=this._y, r;if(typeof s[y]==="string")s[y]=s[y].split(" ").reverse();r=s[y].pop();if(!s[y].length)this._y++;return f?r:+r;};g.prototype.l=function(f){var s=this._s[this._y++].split(" ");return f?s:s.map(a=>+a);};g.prototype.m=function(n,f){var r=this._s.slice(this._y,this._y+=n).map(a=>a.split(" "));return f?r:r.map(a=>a.map(a=>+a));};g.prototype.r=function(n,f){var r=this._s.slice(this._y,this._y+=n);return f?r:r.map(a=>+a);};return f;})();
var o=GET(require("fs").readFileSync("/dev/stdin","utf8"));
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill(0).map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill(0).map(x=>"+r+")";return eval(r);}
var mod = 1e9+7;

console.log(main());
function main(){
  var n = o.a();
  var k = o.a();
  var mx = Math.min(n*n>>1,k);
  if(k%2 !== 0 || k > mx)return 0;
  var n2 = n>>1;
  var dp = xArray(0,n+2,n2+2,mx+n+2);
  dp[0][0][0] = 1;
  for(var i = 0; i < n; i++)
  for(var j = 0; j <= n2; j++)
  for(var x = 0; x <= mx; x += 2){
    dp[i][j][x] %= mod;
    dp[i+1][j][x+j+j] += dp[i][j][x] * (j+j+1);
    if(j)dp[i+1][j-1][x+j+j-2] += dp[i][j][x] * j * j;
    dp[i+1][j+1][x+j+j+2] += dp[i][j][x];
  }
  return dp[n][0][k]%mod;
}