var GET=(function(){function f(s){return new g(s);}function g(s){this._s=s.trim().split("\n");this._y=0;}g.prototype.a=function(f){var s=this._s, y=this._y, r;if(typeof s[y]==="string")s[y]=s[y].split(" ").reverse();r=s[y].pop();if(!s[y].length)this._y++;return f?r:+r;};g.prototype.l=function(f){var s=this._s[this._y++].split(" ");return f?s:s.map(a=>+a);};g.prototype.m=function(n,f){var r=this._s.slice(this._y,this._y+=n).map(a=>a.split(" "));return f?r:r.map(a=>a.map(a=>+a));};g.prototype.r=function(n,f){var r=this._s.slice(this._y,this._y+=n);return f?r:r.map(a=>+a);};return f;})();
var o=GET(require("fs").readFileSync("/dev/stdin","utf8"));

console.log(main());
function main(){
  var n = o.a();
  var k = o.a();
  var a = o.l();
  var b = [];
  for(var i = 0; i < n; i++)b[i] = [a[i], i+1];
  b.sort((a,b)=>b[0]-a[0]);
  var ans = [];
  for(i = 0; i < n; i++){
    b[i][0]--;
    ans.push(b[i][1]);
  }
  var f = b[n-1][1];
  for(;k > 0; k--){
    b.sort((a,b)=>b[0]-a[0]);
    for(i = 0; i < n; i++){
      if(f === b[i][1])continue;
      if(b[i][0] <= 0)return -1;
      b[i][0]--;
      ans.push(b[i][1]);
    }
    if(f === b[n-1][1])f = b[n-2][1];
    else f = b[n-1][1];
  }
  console.log(ans.length);
  return ans.join(" ");
}