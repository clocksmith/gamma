"use strict";
var GET=(function(){function f(s){return new g(s);}function g(s){this._s=s.trim().split("\n");this._y=0;}g.prototype.a=function(f){var s=this._s, y=this._y, r;if(typeof s[y]==="string")s[y]=s[y].split(" ").reverse();r=s[y].pop();if(!s[y].length)this._y++;return f?r:+r;};g.prototype.l=function(f){var s=this._s[this._y++].split(" ");return f?s:s.map(a=>+a);};g.prototype.m=function(n,f){var r=this._s.slice(this._y,this._y+=n).map(a=>a.split(" "));return f?r:r.map(a=>a.map(a=>+a));};g.prototype.r=function(n,f){var r=this._s.slice(this._y,this._y+=n);return f?r:r.map(a=>+a);};return f;})();
var o=GET(require("fs").readFileSync("/dev/stdin","utf8"));
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill(0).map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill(0).map(x=>"+r+")";return eval(r);}

var INF = 1e15;

function segTree(n){
  var l = n.length, u = l-1, x = 2, i, v;
  while(u)u >>= 1, x <<= 1;
  v = this.seg = Array(x-1).fill(INF);
  this.l = x = (x >> 1) - 1;
  for(i = 0; i < l; i++)v[i+x] = n[i];
  for(i = x-1; i >= 0; i--)v[i] = segSolve(v[i+i+1],v[i+1<<1]);
}
function segSolve(a,b){
  return Math.min(a,b);
}
segTree.prototype={
  get:function(l,r){//[l,r)
    if(l >= r)return 0;
    var v = this.seg;
    return q(l,r,0,this.l+1,0);
    function q(l,r,x,y,i){
      if(l === x && r === y)return v[i];
      var m = x+y >> 1;
      if(m < r)if(l < m)return segSolve(q(l,m,x,m,i+i+1),q(m,r,m,y,i+1<<1));
      else return q(l,r,m,y,i+1<<1);
      return q(l,r,x,m,i+i+1);
    }
  },
  update:function(x,i){
    var v = this.seg;
    i += this.l;
    v[i] = x;
    for(i = i-1>>1; i >= 0; i = i-1>>1){
      v[i] = segSolve(v[i+i+1],v[i+1<<1]);
    }
  },
}

console.log(main());
function main(){
  var n = o.a();
  var m = o.a();
  var e = o.m(m);
  e.sort((a,b)=>a[0]<b[0]?-1:a[0]>b[0]?1:a[1]-b[1]);
  var seg = new segTree(xArray(INF,n));
  seg.update(0,0);
  for(var i = 0; i < m; i++){
    var l = e[i][0], r = e[i][1], c = e[i][2];
    l--, r--;
    var cost = seg.get(l,r+1)+c;
    if(seg.get(r,r+1) > cost)seg.update(cost,r);
  }
  var ans = seg.get(n-1,n);
  if(ans >= 1e15)return -1;
  return ans;
}