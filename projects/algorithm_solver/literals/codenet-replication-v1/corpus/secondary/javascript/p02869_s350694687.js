"use strict";
var GET=(function(){function f(s){return new g(s);}function g(s){this._s=s.trim().split("\n");this._y=0;}g.prototype.a=function(f){var s=this._s, y=this._y, r;if(typeof s[y]==="string")s[y]=s[y].split(" ").reverse();r=s[y].pop();if(!s[y].length)this._y++;return f?r:+r;};g.prototype.l=function(f){var s=this._s[this._y++].split(" ");return f?s:s.map(a=>+a);};g.prototype.m=function(n,f){var r=this._s.slice(this._y,this._y+=n).map(a=>a.split(" "));return f?r:r.map(a=>a.map(a=>+a));};g.prototype.r=function(n,f){var r=this._s.slice(this._y,this._y+=n);return f?r:r.map(a=>+a);};return f;})();
var o=GET(require("fs").readFileSync("/dev/stdin","utf8"));
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill(0).map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill(0).map(x=>"+r+")";return eval(r);}

console.log(main());
function main(){
  var n = o.a();
  var k = o.a();
  if(2*k-1 > n)return -1;
  var ans = [];
  var c = k+n*3-1, b = c-n, a = k+(n>>1);
  for(var i = 0; i < n+1>>1; i++){
    ans.push(a+" "+b+" "+c);
    a++,b-=2,c--;
  }
  b = k+n*2-2, a = k;
  for(;i < n; i++){
    ans.push(a+" "+b+" "+c);
    a++,b-=2,c--;
  }
  return ans.join("\n");
}