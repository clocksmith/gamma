var GET=(function(){function f(s){return new g(s);}function g(s){this._s=s.trim().split("\n");this._y=0;}g.prototype.a=function(f){var s=this._s, y=this._y, r;if(typeof s[y]==="string")s[y]=s[y].split(" ").reverse();r=s[y].pop();if(!s[y].length)this._y++;return f?r:+r;};g.prototype.l=function(f){var s=this._s[this._y++].split(" ");return f?s:s.map(a=>+a);};g.prototype.m=function(n,f){var r=this._s.slice(this._y,this._y+=n).map(a=>a.split(" "));return f?r:r.map(a=>a.map(a=>+a));};g.prototype.r=function(n,f){var r=this._s.slice(this._y,this._y+=n);return f?r:r.map(a=>+a);};return f;})();
var o=GET(require("fs").readFileSync("/dev/stdin","utf8"));
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill(0).map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill(0).map(x=>"+r+")";return eval(r);}

console.log(main());
function main(){
  var s = o.a(1);
  var n = s.length;
  var k = o.a();
  var ans = 0, t = s[0], u = 1;
  var a = [];
  for(var i = 1; i < n; i++){
    if(t === s[i])u++;
    else{
      a.push(u);
      ans += Math.floor(u/2);
      u = 1;
      t = s[i];
    }
  }
  a.push(u);
  ans += Math.floor(u/2);
  if(k === 1)return ans;
  if(s[0] !== s[n-1])return ans*k;
  if(a.length === 1)return Math.floor(a[0]*k/2);
  ans = 0;
  var m = a.length;
  for(var i = 1; i < m-1; i++){
    ans += Math.floor(a[i]/2);
  }
  ans *= k;
  ans += Math.floor(a[0]/2);
  ans += Math.floor(a[m-1]/2);
  ans += Math.floor((a[0]+a[m-1])/2)*(k-1);
  return ans;
}