var GET=(function(){function f(s){return new g(s);}function g(s){this._s=s.trim().split("\n");this._y=0;}g.prototype.a=function(f){var s=this._s, y=this._y, r;if(typeof s[y]==="string")s[y]=s[y].split(" ").reverse();r=s[y].pop();if(!s[y].length)this._y++;return f?r:+r;};g.prototype.l=function(f){var s=this._s[this._y++].split(" ");return f?s:s.map(a=>+a);};g.prototype.m=function(n,f){var r=this._s.slice(this._y,this._y+=n).map(a=>a.split(" "));return f?r:r.map(a=>a.map(a=>+a));};g.prototype.r=function(n,f){var r=this._s.slice(this._y,this._y+=n);return f?r:r.map(a=>+a);};return f;})();
var o=GET(require("fs").readFileSync("/dev/stdin","utf8"));
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill(0).map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill(0).map(x=>"+r+")";return eval(r);}
var mod = 998244353;

console.log(main());
function main(){
  var n = o.a();
  var x = o.a(1).split("").map(a=>+a);
  var ans = 0;
  for(var i = 0; i < n; i++){
    ans = ans*2 + x[i];
    ans %= mod;
  }
  ans++;
  ans *= n*2;
  var a = odd(n);
  var al = a.length;
  var map = new Map();
  for(var j = 0; j < al; j++){
    var b = 0, m = n/a[j];
    for(var i = 0; i < m; i++){
      b = b*2 + x[i];
      b %= mod;
    }
    var xor = 0;
    for(;i < n; i++){
      if(i%m === 0)xor ^= 1;
      if((x[i%m]^xor) === x[i])continue;
      if(x[i] === 1)b++;
      break;
    }
    if(i === n)b++;
    for(k of map){
      if(m % k[0])continue;
      b -= k[1];
    }
    map.set(m,b);
    ans -= (n-m)*2*b;
  }
  ans %= mod;
  return ans<0?ans+mod:ans;
}

function odd(n){
  var r = [];
  while(n%2 === 0)n >>= 1;
  for(var i = 3; i*i < n; i++){
    if(n%i)continue;
    r.push(i,n/i);
  }
  if(i*i === n)r.push(i);
  if(n > 1)r.push(n);
  return r.sort((a,b)=>b-a);
}