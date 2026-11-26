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

console.log(main());
function main(){
  var n = o.a();
  var k = o.a();
  if(k % 2 === 1)return Math.pow(Math.floor(n/k),3);
  return Math.pow(Math.floor((2*n+k)/2/k),3)+Math.pow(Math.floor(n/k),3);
}