var GET=(function(){function f(s){return new g(s);}function g(s){this._s=s.trim().split("\n");this._y=0;}g.prototype.a=function(f){var s=this._s, y=this._y, r;if(typeof s[y]==="string")s[y]=s[y].split(" ").reverse();r=s[y].pop();if(!s[y].length)this._y++;return f?r:+r;};g.prototype.l=function(f){var s=this._s[this._y++].split(" ");return f?s:s.map(a=>+a);};g.prototype.m=function(n,f){var r=this._s.slice(this._y,this._y+=n).map(a=>a.split(" "));return f?r:r.map(a=>a.map(a=>+a));};g.prototype.r=function(n,f){var r=this._s.slice(this._y,this._y+=n);return f?r:r.map(a=>+a);};return f;})();
var o=GET(require("fs").readFileSync("/dev/stdin","utf8"));
var mod = 998244353;

console.log(main());
function main(){
  var s = o.a(1);
  var sl = s.length;
  var r = +s[0], b = 2 - r, l = 0;
  var ans = [0,0];
  if(r)ans[1] = 1;
  if(b)ans[0] = 1, b--;else l = 1;
  for(var i = 1; i < sl; i++){
    r += +s[i], b += 2 - s[i];
    if(b)b--; else l++;
    var a = Array(r+1).fill(0);
    var t = Math.min(i+1, r);
    for(var j = l; j <= t; j++){
      a[j] = ((ans[j-1]|0) + (ans[j]|0)) % mod;
    }
    ans = a;
  }
  r++;
  for(var i = 0; i < sl; i++){
    if(b)b--; else l++;
    var a = Array(r).fill(0);
    for(var j = l; j < r; j++){
      a[j] = ((ans[j-1]|0) + (ans[j]|0)) % mod;
    }
    ans = a;
  }
  return ans[r-1];
}