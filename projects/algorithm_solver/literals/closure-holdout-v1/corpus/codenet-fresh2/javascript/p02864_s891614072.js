"use strict";
var GET=(function(){function f(s){return new g(s);}function g(s){this._s=s.trim().split("\n");this._y=0;}g.prototype.a=function(f){var s=this._s, y=this._y, r;if(typeof s[y]==="string")s[y]=s[y].split(" ").reverse();r=s[y].pop();if(!s[y].length)this._y++;return f?r:+r;};g.prototype.l=function(f){var s=this._s[this._y++].split(" ");return f?s:s.map(a=>+a);};g.prototype.m=function(n,f){var r=this._s.slice(this._y,this._y+=n).map(a=>a.split(" "));return f?r:r.map(a=>a.map(a=>+a));};g.prototype.r=function(n,f){var r=this._s.slice(this._y,this._y+=n);return f?r:r.map(a=>+a);};return f;})();
var o=GET(require("fs").readFileSync("/dev/stdin","utf8"));
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill(0).map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill(0).map(x=>"+r+")";return eval(r);}
var INF = 1e15;

console.log(main());
function main(){
  var n = o.a();
  var x = o.a();
  var h = [0].concat(o.l());
  var dp = xArray(INF,2,2);
  dp[0][0] = h[1];
  dp[1][1] = 0;
  for(var i = 1; i < n; i++){
    var mn = Math.min(i,x)+1;
    var dp2 = xArray(INF,mn+1,mn+1);
    for(var j = 0; j < mn; j++){
      for(var k = j; k < mn; k++){
        var t = Math.max(0,h[i+1] - h[i-j]);
        if(dp[k][j]+t < dp2[k][0])
          dp2[k][0] = dp[k][j]+t;
      }
      if(j < x)for(var k = j; k < mn; k++){
        if(dp[k][j] < dp2[k+1][j+1])
          dp2[k+1][j+1] = dp[k][j];
      }
    }
    dp = dp2;
  }
  var ans = INF;
  for(var i = 0; i <= x; i++){
    if(dp[x][i] < ans)ans = dp[x][i];
  }
  return ans;
}