var GET=(function(){function f(s){return new g(s);}function g(s){this._s=s.trim().split("\n");this._y=0;}g.prototype.a=function(f){var s=this._s, y=this._y, r;if(typeof s[y]==="string")s[y]=s[y].split(" ").reverse();r=s[y].pop();if(!s[y].length)this._y++;return f?r:+r;};g.prototype.l=function(f){var s=this._s[this._y++].split(" ");return f?s:s.map(a=>+a);};g.prototype.m=function(n,f){var r=this._s.slice(this._y,this._y+=n).map(a=>a.split(" "));return f?r:r.map(a=>a.map(a=>+a));};g.prototype.r=function(n,f){var r=this._s.slice(this._y,this._y+=n);return f?r:r.map(a=>+a);};return f;})();
var o=GET(require("fs").readFileSync("/dev/stdin","utf8"));
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill(0).map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill(0).map(x=>"+r+")";return eval(r);}
function Z_Algorithm(s){
  var l=s.length,a=Array(l);
  a[0]=l;
  for(var i=1,j=0;i<l;){
    while(i+j<l && s[j]===s[i+j])++j;
    a[i]=j;
    if(j === 0){++i; continue;}
    var k=1;
    while(i+k<l && k+a[k]<j)a[i+k]=a[k], ++k;
    i += k; j -= k;
  }
  return a;
}

console.log(main());
function main(){
  var n = o.a();
  var s = o.a(1);
  var ans = 0;
  for(var i = 0; i < n-ans*2; i++){
    var a = Z_Algorithm(s.slice(i));
    for(var j = ans+1; j < a.length; j++){
      var t = Math.min(j,a[j]);
      if(ans < t)ans = t;
    }
  }
  return ans;
}