"use strict";
var GET=(function(){function f(s){return new g(s);}function g(s){this._s=s.trim().split("\n");this._y=0;}g.prototype.a=function(f){var s=this._s, y=this._y, r;if(typeof s[y]==="string")s[y]=s[y].split(" ").reverse();r=s[y].pop();if(!s[y].length)this._y++;return f?r:+r;};g.prototype.l=function(f){var s=this._s[this._y++].split(" ");return f?s:s.map(a=>+a);};g.prototype.m=function(n,f){var r=this._s.slice(this._y,this._y+=n).map(a=>a.split(" "));return f?r:r.map(a=>a.map(a=>+a));};g.prototype.r=function(n,f){var r=this._s.slice(this._y,this._y+=n);return f?r:r.map(a=>+a);};return f;})();
var o=GET(require("fs").readFileSync("/dev/stdin","utf8"));
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill(0).map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill(0).map(x=>"+r+")";return eval(r);}
var priorityQueue=(function(){
  function f(){return new PriorityQueue();}
  function PriorityQueue(){
    this.heap=[];
  }
  PriorityQueue.prototype.push=function(x){
    var h=this.heap,i=h.length++,j;
    while(i){
      j=i-1>>1;
      if(h[j][0]<=x[0])break;
      h[i]=h[j],i=j;
    }
    h[i]=x;
  };
  PriorityQueue.prototype.pop=function(){
    var h=this.heap,r=h[0],x=h.pop(),l=h.length,i=0,j;
    if(l===0)return r;
    var k=l>>1;l--;
    while(i<k){
      j=(i<<1)+1;
      if(j<l&&h[j+1][0]<h[j][0])j++;
      if(x[0]<=h[j][0])break;
      h[i]=h[j],i=j;
    }
    h[i]=x;
    return r;
  };
  return f;
})();
function gcd(a,b){return b?gcd(b,a%b):a;}

console.log(main());
function main(){
  var n = o.a();
  var x = o.a();
  var d = o.a();
  if(d === 0){
    if(x === 0)return 1;
    return n+1;
  }
  if(d < 0)x = -x, d = -d;
  var g = gcd(d,Math.abs(x));
  x /= g, d /= g;
  var pq = new priorityQueue();
  var mn = Math.min(d,n);
  var ans = 1, zero = 1;
  for(var i = 0; i < mn; i++){
    var xx = -(i+1)*x%d;
    for(var j = i+1; j <= n; j += d){
      var xj = x*j+xx;
      xj /= d;
      var l = xj+(j-1)*j/2;
      var r = xj+j*n-(j+1)*j/2;
      if(zero && xx === 0 && l <= 0 && r >= 0)ans--, zero = 0;
      pq.push([l,r]);
    }
    var p = pq.pop();
    while(pq.heap.length){
      var t = pq.pop();
      if(t[0] <= p[1])p[1] = Math.max(p[1],t[1]);
      else{
        ans += 1+p[1]-p[0];
        p = t;
      }
    }
    ans += 1+p[1]-p[0];
  }
  return ans;
}