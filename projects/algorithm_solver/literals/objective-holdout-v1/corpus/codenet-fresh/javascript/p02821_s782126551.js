"use strict";
var GET=(function(){function f(s){return new g(s);}function g(s){this._s=s.trim().split("\n");this._y=0;}g.prototype.a=function(f){var s=this._s, y=this._y, r;if(typeof s[y]==="string")s[y]=s[y].split(" ").reverse();r=s[y].pop();if(!s[y].length)this._y++;return f?r:+r;};g.prototype.l=function(f){var s=this._s[this._y++].split(" ");return f?s:s.map(a=>+a);};g.prototype.m=function(n,f){var r=this._s.slice(this._y,this._y+=n).map(a=>a.split(" "));return f?r:r.map(a=>a.map(a=>+a));};g.prototype.r=function(n,f){var r=this._s.slice(this._y,this._y+=n);return f?r:r.map(a=>+a);};return f;})();
var o=GET(require("fs").readFileSync("/dev/stdin","utf8"));
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill(0).map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill(0).map(x=>"+r+")";return eval(r);}
function lower_bound(d,a,b,e){for(var c;1<b-a;)d[c=a+b>>1]<e?a=c:b=c;return d[a]<e?b:a};

console.log(main());
function main(){
  var n = o.a(), m = o.a();
  var a = o.l();
  a.sort((a,b)=>a-b);
  var ok = 0, ng = a[n-1]*2+1;
  while(ng-ok > 1){
    var mid = ok+ng >> 1;
    var cnt = n*n;
    for(var i = 0; i < n; i++){
      cnt -= lower_bound(a,0,n,mid-a[i]);
    }
    if(cnt >= m)ok = mid;
    else ng = mid;
  }
  var b = Array(n+1);
  b[0] = 0;
  for(var i = 0; i < n; i++)b[i+1] = b[i]+a[i];
  var ans = 0;
  var cnt = n*n;
  for(var i = 0; i < n; i++){
    var id = lower_bound(a,0,n,ok-a[i]+1);
    cnt -= id;
    ans += a[i]*(n-id) + b[n] - b[id];
  }
  return ans + (m-cnt) * ok;
}