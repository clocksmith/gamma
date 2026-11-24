function gets(str){
  this._s = str.split("\n");
  this._y = 0;
};
gets.prototype = {
  a: function(f){
    var s = this._s, y = this._y, r;
    if(typeof s[y] === "string")s[y] = s[y].split(" ").reverse();
    r = s[y].pop();
    if(!s[y].length)this._y++;
    return f?r:+r;
  },
  l: function(f){
    var s = this._s[this._y++].split(" ");
    return f?s:s.map(a=>+a);
  },
  m: function(n,f){
    var s = this._s, y = this._y, r = [], i = 0;
    if(f)for(;i < n; i++)r[i] = s[y+i].split(" ");
    else for(;i < n; i++)r[i] = s[y+i].split(" ").map(a=>+a);
    this._y += n;
    return r;
  },
};
var o=new gets(require("fs").readFileSync("/dev/stdin","utf8"));
function gcd(a,b){return b?gcd(b,a%b):a;}

console.log(main());
function main(){
  var n = o.a();
  var m = o.a();
  var s = o.a(1);
  var t = o.a(1);
  var g = gcd(n,m);
  var h = n * m / g;
  n /= g;
  m /= g;
  for(var i = 0; i < g; i++){
    if(s[i*n] !== t[i*m])return -1;
  }
  return h;
}