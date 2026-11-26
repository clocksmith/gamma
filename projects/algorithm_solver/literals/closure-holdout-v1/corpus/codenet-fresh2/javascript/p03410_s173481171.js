var GET=(function(){function f(s){return new g(s);}function g(s){this._s=s.trim().split("\n");this._y=0;}g.prototype.a=function(f){var s=this._s, y=this._y, r;if(typeof s[y]==="string")s[y]=s[y].split(" ").reverse();r=s[y].pop();if(!s[y].length)this._y++;return f?r:+r;};g.prototype.l=function(f){var s=this._s[this._y++].split(" ");return f?s:s.map(a=>+a);};g.prototype.m=function(n,f){var r=this._s.slice(this._y,this._y+=n).map(a=>a.split(" "));return f?r:r.map(a=>a.map(a=>+a));};g.prototype.r=function(n,f){var r=this._s.slice(this._y,this._y+=n);return f?r:r.map(a=>+a);};return f;})();
var o=GET(require("fs").readFileSync("/dev/stdin","utf8"));

console.log(main());
function main(){
  var n = o.a();
  var a = o.l();
  var b = o.l();
  var ans = 0;
  for(var i = 28; i >= 0; i--){
    if(i < 17)b = f(b,i), a = f(a,i).reverse();
    else {b.sort((a,b)=>a-b); a.sort((a,b)=>b-a);}
    var t = 1 << i, t2 = t << 1, t3 = t*3, x = n, x1, x2, x3;
    x1 = x2 = x3 = 0;
    for(var j = 0; j < a.length; j++){
      while(x1 < b.length && t-a[j] > b[x1])x1++;
      while(x2 < b.length && t2-a[j] > b[x2])x2++;
      while(x3 < b.length && t3-a[j] > b[x3])x3++;
      x += -x3+x2-x1;
    }
    if(x % 2)ans += t;
    t--;
    b = b.map(a=>a&t);
    a = a.map(a=>a&t);
  }
  return ans;

  function f(b,n){
    var a = Array(1<<n+1).fill(0), r = [];
    for(var i = 0; i < b.length; i++){
      a[b[i]]++;
    }
    for(i = 0; i < a.length; i++)if(a[i]&1)r.push(i);
    return r;
  }
}