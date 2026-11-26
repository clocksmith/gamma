var GET=(function(){function f(s){return new g(s);}function g(s){this._s=s.trim().split("\n");this._y=0;}g.prototype.a=function(f){var s=this._s, y=this._y, r;if(typeof s[y]==="string")s[y]=s[y].split(" ").reverse();r=s[y].pop();if(!s[y].length)this._y++;return f?r:+r;};g.prototype.l=function(f){var s=this._s[this._y++].split(" ");return f?s:s.map(a=>+a);};g.prototype.m=function(n,f){var r=this._s.slice(this._y,this._y+=n).map(a=>a.split(" "));return f?r:r.map(a=>a.map(a=>+a));};g.prototype.r=function(n,f){var r=this._s.slice(this._y,this._y+=n);return f?r:r.map(a=>+a);};return f;})();
var o=GET(require("fs").readFileSync("/dev/stdin","utf8"));

console.log(main());
function main(){
  var n = o.a();
  var m = o.a();
  var v = Array(n+1).fill(0).map(a=>[]);
  for(var i = 0; i < m; i++){
    var t = o.l();
    v[t[0]].push(t[1]);
    v[t[1]].push(t[0]);
  }
  var f = 0, s = 0, q = [];
  for(i = 1; i <= n; i++){
    var a = v[i].length;
    if(a & 1)return "No";
    if(a >= 6)s = 1;
    if(a === 4){q.push(i);}
  }
  return dfs() ? "Yes" : "No";

  function dfs(){
    if(s || q.length > 2)return 1;
    if(q.length < 2)return;
    var x = q[0], y = q[1];
    for(var i = 0; i < 3; i++){
      var b = v[x][i], c = x;
      while(b !== y){
        var t = b;
        b = v[b][0] + v[b][1] - c;
        c = t;
        if(b === x)return 1;
      }
    }
  }
}