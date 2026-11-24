var GET = (function(){
  function f(s){return new g(s);}
  function g(s){this._s=s.trim().split("\n");this._y=0;}
  g.prototype.a = function(f){
    var s = this._s, y = this._y, r;
    if(typeof s[y] === "string")s[y]=s[y].split(" ").reverse();
    r = s[y].pop();
    if(!s[y].length)this._y++;
    return f?r:+r;
  }
  g.prototype.l = function(f){
    var s=this._s[this._y++].split(" ");return f?s:s.map(a=>+a);
  }
  g.prototype.m = function(n,f){
    var r=this._s.slice(this._y,this._y+=n).map(a=>a.split(" "));
    return f?r:r.map(a=>a.map(a=>+a));
  }
  g.prototype.r = function(n,f){
    var r = this._s.slice(this._y,this._y+=n);
    return f?r:r.map(a=>+a);
  }
  return f;
})();
var o=GET(require("fs").readFileSync("/dev/stdin","utf8"));

console.log(main());
function main(){
  var n = o.a();
  var k = o.a();
  var a = o.l();
  var s = [0];
  for(var i = 0; i < n;i++)s[i+1] = s[i] + a[i];
  var w = [];
  for(var l = 0; l < n; l++){
    for(var r = l+1; r <= n; r++){
      var t = s[r]-s[l];
      w.push(t);
    }
  }
  var ans = 0;
  for(i = 39; i > 30; i--){
    var t = [], z = Math.pow(2,i);
    for(var j = 0; j < w.length; j++){
      if((w[j] / z | 0) & 1)t.push(w[j]);
    }
    if(t.length >= k){ans += z; w = t;}
  }
  for(;i >= 0; i--){
    var t = [], z = 1 << i;
    for(j = 0; j < w.length; j++){
      if((z & w[j]) !== 0)t.push(w[j]);
    }
    if(t.length >= k){ans += z; w = t;}
  }
  return ans;
}