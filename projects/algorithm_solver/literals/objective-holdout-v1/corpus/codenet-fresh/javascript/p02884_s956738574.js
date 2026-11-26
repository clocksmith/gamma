"use strict";
var GET=(function(){function f(s){return new g(s);}function g(s){this._s=s.trim().split("\n");this._y=0;}g.prototype.a=function(f){var s=this._s, y=this._y, r;if(typeof s[y]==="string")s[y]=s[y].split(" ").reverse();r=s[y].pop();if(!s[y].length)this._y++;return f?r:+r;};g.prototype.l=function(f){var s=this._s[this._y++].split(" ");return f?s:s.map(a=>+a);};g.prototype.m=function(n,f){var r=this._s.slice(this._y,this._y+=n).map(a=>a.split(" "));return f?r:r.map(a=>a.map(a=>+a));};g.prototype.r=function(n,f){var r=this._s.slice(this._y,this._y+=n);return f?r:r.map(a=>+a);};return f;})();
var o=GET(require("fs").readFileSync("/dev/stdin","utf8"));
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill(0).map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill(0).map(x=>"+r+")";return eval(r);}

console.log(main());
function main(){
  var n = o.a();
  var m = o.a();
  var x = o.m(m);
  var map = xArray("[]",n);
  for(var i = 0; i < m; i++){
    var s = x[i][0]-1, t = x[i][1]-1;
    map[s].push(t);
  }
  var dp = xArray(0,n);
  for(var i = n-1; i--;){
    var c = 1/map[i].length;
    for(var j = map[i].length; j--;){
      dp[i] += (dp[map[i][j]]+1) * c;
    }
  }
  var ans = dp[0];
  var dp2 = dp.concat();
  for(var i = n-2; i--;){
    dp[i+1] = dp2[i+1];
    if(map[i].length === 1)continue;
    dp[i] = 0;
    var mx = 0, id;
    var c = 1/(map[i].length-1);
    for(var j = map[i].length; j--;){
      if(dp[map[i][j]] > mx)mx = dp[map[i][j]], id = j;
    }
    for(var j = map[i].length; j--;){
      if(j === id)continue;
      dp[i] += (dp[map[i][j]]+1) * c;
    }
    for(var k = i; k--;){
      var c = 1/map[k].length;
      dp[k] = 0;
      for(var j = map[k].length; j--;){
        dp[k] += (dp[map[k][j]]+1) * c;
      }
    }
    if(dp[0] < ans)ans = dp[0];
  }
  return ans;
}