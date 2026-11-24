var GET=(function(){function f(s){return new g(s);}function g(s){this._s=s.trim().split("\n");this._y=0;}g.prototype.a=function(f){var s=this._s, y=this._y, r;if(typeof s[y]==="string")s[y]=s[y].split(" ").reverse();r=s[y].pop();if(!s[y].length)this._y++;return f?r:+r;};g.prototype.l=function(f){var s=this._s[this._y++].split(" ");return f?s:s.map(a=>+a);};g.prototype.m=function(n,f){var r=this._s.slice(this._y,this._y+=n).map(a=>a.split(" "));return f?r:r.map(a=>a.map(a=>+a));};g.prototype.r=function(n,f){var r=this._s.slice(this._y,this._y+=n);return f?r:r.map(a=>+a);};return f;})();
var o=GET(require("fs").readFileSync("/dev/stdin","utf8"));
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill(0).map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill(0).map(x=>"+r+")";return eval(r);}
var n,m,e,a;

console.log(main());
function main(){
  n = o.a();
  m = o.a();
  e = xArray("[]",n);
  for(var i = 0; i < m; i++){
    var t = o.l(); t[0]--, t[1]--;
    e[t[0]].push(t[1]);
  }
  var s = o.a()-1;
  var g = o.a()-1;
  a = xArray(0,3,n);
  a[0][s] = 1;
  var q = [s], ans = 0;
  while(q.length){
    ans++;
    for(var i = 0; i < 3; i++){
      q = solve(q,i);
    }
    if(a[0][g])return ans;
  }
  return -1;
}

function solve(q,i){
  var r = [], j = (i+1)%3;
  while(q.length){
    var p = q.pop();
    for(var v of e[p]){
      if(a[j][v])continue;
      r.push(v);
      a[j][v] = 1;
    }
  }
  return r;
}