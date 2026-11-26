var GET=(function(){function f(s){return new g(s);}function g(s){this._s=s.trim().split("\n");this._y=0;}g.prototype.a=function(f){var s=this._s, y=this._y, r;if(typeof s[y]==="string")s[y]=s[y].split(" ").reverse();r=s[y].pop();if(!s[y].length)this._y++;return f?r:+r;};g.prototype.l=function(f){var s=this._s[this._y++].split(" ");return f?s:s.map(a=>+a);};g.prototype.m=function(n,f){var r=this._s.slice(this._y,this._y+=n).map(a=>a.split(" "));return f?r:r.map(a=>a.map(a=>+a));};g.prototype.r=function(n,f){var r=this._s.slice(this._y,this._y+=n);return f?r:r.map(a=>+a);};return f;})();
var o=GET(require("fs").readFileSync("/dev/stdin","utf8"));

console.log(main());
function main(){
  var s = o.a(1);
  var x = [o.a(),o.a()];
  var h = [[],[]], l = s.length;
  var T = "T";
  for(var i = 0; i < l; i++){
    if(s[i] === T)break;
    x[0]--;
  }
  var f = 1, u = 0;
  for(i++; i < l; i++){
    if(s[i] === T){if(u)h[f].push(u); f ^= 1; u = 0;}
    else u++;
  }
  if(u)h[f].push(u);
  for(i = 0; i < 2; i++){
    var set = new Set();
    set.add(x[i]);
    while(h[i].length){
      var t = h[i].pop();
      var set2 = new Set();
      for(var j of set){
        set2.add(j-t);
        set2.add(j+t);
      }
      set = set2;
    }
    if(!set.has(0))return "No";
  }
  return "Yes";
}