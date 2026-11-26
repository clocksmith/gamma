"use strict";
var GET=(function(){function f(s){return new g(s);}function g(s){this._s=s.trim().split("\n");this._y=0;}g.prototype.a=function(f){var s=this._s, y=this._y, r;if(typeof s[y]==="string")s[y]=s[y].split(" ").reverse();r=s[y].pop();if(!s[y].length)this._y++;return f?r:+r;};g.prototype.l=function(f){var s=this._s[this._y++].split(" ");return f?s:s.map(a=>+a);};g.prototype.m=function(n,f){var r=this._s.slice(this._y,this._y+=n).map(a=>a.split(" "));return f?r:r.map(a=>a.map(a=>+a));};g.prototype.r=function(n,f){var r=this._s.slice(this._y,this._y+=n);return f?r:r.map(a=>+a);};return f;})();
var o=GET(require("fs").readFileSync("/dev/stdin","utf8"));
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill(0).map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill(0).map(x=>"+r+")";return eval(r);}

console.log(main());
function main(){
  var n = o.a();
  var a = o.l();
  var map = xArray(0,n);
  for(var i = 0; i < n; i++){
    map[a[i]-1]++;
  }
  var set = [];
  for(var i = 0; i < n; i++){
    if(map[i])set.push(map[i]);
  }
  set.sort((a,b)=>b-a);
  var ans = [n];
  var l = 0, sum = 0;
  for(var i = 2; i <= n; i++){
    if(set.length < i){
      ans.push(0);
      continue;
    }
    var mx = n/i|0;
    while(1){
      while(l < set.length && mx < set[l]){
        sum += set[l];
        l++;
      }
      var nn = n - sum + l*mx;
      var mx2 = nn/i|0;
      if(mx2 === mx)break;
      else mx = mx2;
    }
    ans.push(mx);
  }
  return ans.join("\n");
}